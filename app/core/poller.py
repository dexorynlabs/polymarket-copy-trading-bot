"""Poller — WebSocket subscription to PM activity/trades, dedup, watchdog.

Subscribes once to the global activity/trades stream and filters incoming
events by `proxyWallet` to match the target. App-level `Text("PING")` heartbeat
every 5s (matches PM convention). Fills are dispatched to a bounded asyncio
Queue so the WS receive loop never blocks on `on_fill` (POST /order). PM WS
connections become zombie after ~20 minutes of silence — the silent watchdog
raises to force a supervisor restart.
"""

import asyncio
import contextlib
import json
import logging
import time
from collections import OrderedDict
from typing import Awaitable, Callable

import aiohttp

from app.core.trader import TargetFill


WS_URL = "wss://ws-live-data.polymarket.com"
PING_INTERVAL_S = 5             # app-level Text("PING") cadence
RECONNECT_MIN_SLEEP_S = 1.0     # minimum delay between reconnects even on clean close
FILL_QUEUE_MAX = 256            # bounded queue; overflow → drop + log

log = logging.getLogger("poller")


def _full_row_key(p: dict) -> str:
    """Dedup key: tx_hash + asset + side + size + price (full row, not just tx_hash —
    one taker × N makers produces N rows sharing tx_hash but with different size/price)."""
    return f"{p.get('transactionHash','')}|{p.get('asset','')}|{p.get('side','')}|{p.get('size','')}|{p.get('price','')}"


class LRU:
    """Tiny LRU set with capacity. add() / __contains__, no value storage."""

    def __init__(self, cap: int):
        self.cap = cap
        self._d: OrderedDict[str, bool] = OrderedDict()

    def __contains__(self, key: str) -> bool:
        return key in self._d

    def add(self, key: str) -> None:
        if key in self._d:
            self._d.move_to_end(key)
            return
        self._d[key] = True
        if len(self._d) > self.cap:
            self._d.popitem(last=False)

    def __len__(self) -> int:
        return len(self._d)

    def to_list(self) -> list[str]:
        return list(self._d.keys())

    @classmethod
    def from_list(cls, keys: list[str], cap: int) -> "LRU":
        lru = cls(cap)
        for k in keys:
            lru.add(k)
        return lru


class Poller:
    """WebSocket poller for PM activity/trades stream."""

    def __init__(
        self,
        config: dict,
        session: aiohttp.ClientSession,
        on_fill: Callable[[TargetFill], Awaitable[None]],
        state: dict,
    ):
        self.config = config
        self.session = session
        self.on_fill = on_fill
        self.target = config["target_wallet"].lower()

        self.seen = LRU.from_list(state.get("seen_tx_keys", []), config["dedup"]["seen_cap"])

        # Watchdog state — updated on every WS event (any message type), so we
        # detect zombie connections even when the target isn't trading.
        self.last_event_ms = int(time.time() * 1000)
        self.consecutive_reconnect_errors = 0
        self._state_dirty = False

        # Fills queued from WS receive loop, drained by consumer task.
        # Bounded — overflow is logged and dropped.
        self._fill_queue: asyncio.Queue = asyncio.Queue(maxsize=FILL_QUEUE_MAX)
        self._dropped_fills = 0

    # ── State ──

    def export_state(self) -> dict:
        return {"seen_tx_keys": self.seen.to_list()}

    @property
    def dirty(self) -> bool:
        return self._state_dirty

    def mark_clean(self) -> None:
        self._state_dirty = False

    # ── Main run loop with reconnect ──

    async def run(self, shutdown: asyncio.Event) -> None:
        # Start fill-queue consumer (separate from receive loop so on_fill
        # latency doesn't block WS message processing).
        consumer_task = asyncio.create_task(self._consumer_loop(shutdown), name="fill-consumer")
        try:
            await self._reconnect_loop(shutdown)
        finally:
            consumer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await consumer_task

    async def _reconnect_loop(self, shutdown: asyncio.Event) -> None:
        max_errs = self.config["watchdog"]["max_consecutive_errors"]
        while not shutdown.is_set():
            try:
                await self._run_connection(shutdown)
                self.consecutive_reconnect_errors = 0
                # Even on clean close, pause briefly to avoid tight-loop
                # reconnects if the server flaps.
                try:
                    await asyncio.wait_for(shutdown.wait(), timeout=RECONNECT_MIN_SLEEP_S)
                    return
                except asyncio.TimeoutError:
                    pass
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.consecutive_reconnect_errors += 1
                backoff_s = min(2 ** min(self.consecutive_reconnect_errors, 5), 30)
                log.warning(
                    f"[WS-ERROR] {type(e).__name__}: {e} "
                    f"(consecutive={self.consecutive_reconnect_errors}, "
                    f"backoff={backoff_s}s)"
                )
                if self.consecutive_reconnect_errors == max_errs:
                    log.error(
                        f"[WS] {self.consecutive_reconnect_errors} consecutive "
                        f"failures (>= {max_errs}) — still retrying"
                    )
                try:
                    await asyncio.wait_for(shutdown.wait(), timeout=backoff_s)
                    return
                except asyncio.TimeoutError:
                    pass

    async def _run_connection(self, shutdown: asyncio.Event) -> None:
        log.info("Data stream connecting…")
        # Reset watchdog at connect-start so slow handshake doesn't trip it.
        self.last_event_ms = int(time.time() * 1000)

        async with self.session.ws_connect(WS_URL, timeout=10) as ws:
            sub = {
                "action": "subscribe",
                "subscriptions": [{"topic": "activity", "type": "trades"}],
            }
            await ws.send_str(json.dumps(sub))
            log.info(f"Subscribed target: {self.target}")
            self.last_event_ms = int(time.time() * 1000)

            # App-level heartbeat: PM expects Text("PING"), not WS frame ping.
            ping_task = asyncio.create_task(self._ping_loop(ws), name="ws-ping")
            try:
                async for msg in ws:
                    if shutdown.is_set():
                        return
                    mt = msg.type
                    if mt == aiohttp.WSMsgType.TEXT:
                        await self._handle_text(msg.data)
                    elif mt in (
                        aiohttp.WSMsgType.PING,
                        aiohttp.WSMsgType.PONG,
                        aiohttp.WSMsgType.BINARY,
                    ):
                        # Any inbound traffic = alive
                        self.last_event_ms = int(time.time() * 1000)
                    elif mt in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSING,
                        aiohttp.WSMsgType.CLOSE,
                    ):
                        log.warning("[WS] connection closed by remote")
                        return
                    elif mt == aiohttp.WSMsgType.ERROR:
                        log.warning(f"[WS] error: {ws.exception()}")
                        return
            finally:
                ping_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await ping_task

    async def _ping_loop(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        """App-level heartbeat — PM convention: send Text("PING") every 5s,
        server replies Text("PONG"). Loop exits when connection breaks."""
        while True:
            await asyncio.sleep(PING_INTERVAL_S)
            try:
                await ws.send_str("PING")
            except (aiohttp.ClientError, ConnectionResetError):
                return

    # ── Message handling (WS receive side) ──

    async def _handle_text(self, raw: str) -> None:
        # Any TEXT message counts as alive for watchdog.
        self.last_event_ms = int(time.time() * 1000)

        # PM may send bare PING / PONG / empty keepalive strings — ignore.
        stripped = raw.strip()
        if stripped in ("PING", "PONG", "ping", "pong", ""):
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        if data.get("topic") != "activity" or data.get("type") != "trades":
            return

        # Envelope timestamp (ms, 13-digit) = when PM pushed the event.
        # More accurate for lag measurement than payload.timestamp (sec).
        envelope_ts_ms = data.get("timestamp", 0)

        payload = data.get("payload") or {}
        wallet = (payload.get("proxyWallet") or "").lower()
        if wallet != self.target:
            return    # not our target

        key = _full_row_key(payload)
        if key in self.seen:
            return    # already processed

        self.seen.add(key)
        self._state_dirty = True

        fill = self._parse_fill(payload, envelope_ts_ms)
        now_ms = int(time.time() * 1000)
        lag_ms = (now_ms - fill.timestamp_ms) if fill.timestamp_ms > 0 else -1
        log.info(
            f"[NEW] tx={fill.tx_hash[:10]}… {fill.side} asset={fill.asset[:12]}… "
            f"size={fill.size:.2f} px={fill.price:.4f} lag={lag_ms}ms "
            f"slug={fill.market_slug}"
        )

        # Enqueue for the consumer task — never block the WS receive loop.
        try:
            self._fill_queue.put_nowait(fill)
        except asyncio.QueueFull:
            self._dropped_fills += 1
            log.error(
                f"[FILL-QUEUE-FULL] dropping fill tx={fill.tx_hash[:10]}… "
                f"queue_size={self._fill_queue.qsize()} total_dropped={self._dropped_fills}"
            )

    async def _consumer_loop(self, shutdown: asyncio.Event) -> None:
        """Drains the fill queue and calls on_fill — runs independently of
        the WS receive loop so a slow POST /order doesn't block message read."""
        while not shutdown.is_set():
            try:
                fill = await asyncio.wait_for(self._fill_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            try:
                await self.on_fill(fill)
            except Exception as e:
                log.exception(f"on_fill handler raised: {e}")

    @staticmethod
    def _parse_fill(p: dict, envelope_ts_ms: int) -> TargetFill:
        """
        Normalize a PM activity/trades payload into a TargetFill.

        We use the ENVELOPE timestamp (ms, when PM pushed) for `timestamp_ms`
        because it gives accurate "PM publish → bot recv" latency. The
        payload.timestamp is unix SECONDS (1s quantization, 0-999ms noise)
        and unsuitable for lag measurement. Fall back to payload.timestamp
        if envelope ts is missing/zero.
        """
        try:
            ts_ms = int(envelope_ts_ms or 0)
        except (TypeError, ValueError):
            ts_ms = 0
        if ts_ms < 10**11:    # envelope absent or in seconds — fall back to payload
            ts_raw = p.get("timestamp", 0) or 0
            try:
                ts_num = float(ts_raw)
            except (TypeError, ValueError):
                ts_num = 0.0
            ts_ms = int(ts_num if ts_num >= 1e11 else ts_num * 1000)

        return TargetFill(
            tx_hash=p.get("transactionHash", ""),
            asset=str(p.get("asset", "")),
            market_slug=p.get("slug", "") or p.get("eventSlug", ""),
            side=(p.get("side") or "").upper(),
            size=float(p.get("size", 0) or 0),
            price=float(p.get("price", 0) or 0),
            price_str=str(p.get("price", "")),
            timestamp_ms=ts_ms,
        )

    # ── Silent-freeze watchdog ──

    async def silent_watchdog(self, shutdown: asyncio.Event) -> None:
        """
        If no WS event arrives in N seconds, abort the bot. PM activity is a
        global firehose — events flow continuously regardless of target's trading.
        Silence = zombie connection; raise to trigger graceful shutdown so a
        supervisor (systemd / operator) can restart with a fresh socket.
        """
        timeout_ms = self.config["watchdog"]["silent_timeout_s"] * 1000
        while not shutdown.is_set():
            try:
                await asyncio.wait_for(shutdown.wait(), timeout=5)
                return
            except asyncio.TimeoutError:
                pass
            silent_ms = int(time.time() * 1000) - self.last_event_ms
            if silent_ms > timeout_ms:
                msg = (
                    f"[WATCHDOG] No WS event in {silent_ms / 1000:.1f}s "
                    f"(threshold {timeout_ms / 1000:.0f}s) — exiting for supervisor restart"
                )
                log.error(msg)
                raise RuntimeError(msg)
