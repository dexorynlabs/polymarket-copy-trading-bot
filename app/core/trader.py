"""Trader — batching accumulator, translator, sizing, PositionTracker.

Decision pipeline per target fill:
  consume_chunk_if_ready → sizing → translate → clob.place_order
                                                       ↓
                              PositionTracker.add  (+async Gamma endDate fetch)
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.pm.clob import ClobClient, OrderSpec, OrderResult


DEFAULT_TICK = 0.01   # fallback when target fill price gives no info ("0.5")
CLOB_MIN_SHARES = 5.0

# PM binary outcome: price ∈ (0, 1) exclusive of $1. The highest valid limit is
# (1 - tick). Hardcoded exact values avoid float-imprecision from `1.0 - tick`:
#   1.0 - 0.001 → 0.999 (usually safe but not guaranteed bit-exact)
#   1.0 - 0.0001 → 0.9999 (also fine — but kept explicit for clarity).
TICK_MAX_PRICE = {
    0.01:   0.99,
    0.001:  0.999,
    0.0001: 0.9999,
}

log = logging.getLogger("trader")


# ──────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────


@dataclass
class TargetFill:
    """Normalized target fill from PM activity/trades WS event."""
    tx_hash: str
    asset: str             # token_id
    market_slug: str
    side: str              # "BUY" or "SELL"
    size: float
    price: float
    price_str: str         # original string for tick inference
    timestamp_ms: int


@dataclass
class PositionEntry:
    asset_id: str
    market_slug: str
    cost_basis_usd: float
    opened_at_ms: int
    end_date_ms: Optional[int] = None    # populated async via Gamma
    order_id: Optional[str] = None       # CLOB orderID (None in dry_run sim)


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


def infer_tick_from_price(price_str: str) -> float:
    """
    "0.42"   → 0.01
    "0.435"  → 0.001
    "0.4321" → 0.0001
    "0.5"    → DEFAULT_TICK (no info, fallback)
    "0.50"   → DEFAULT_TICK (trailing zero stripped)
    """
    s = str(price_str)
    if "." not in s:
        return DEFAULT_TICK
    decimals = s.split(".")[1].rstrip("0")
    n = len(decimals)
    if n <= 1:
        return DEFAULT_TICK
    if n == 2:
        return 0.01
    if n == 3:
        return 0.001
    return 0.0001


def round_to_tick(price: float, tick: float) -> float:
    """Round price to nearest tick multiple."""
    return round(price / tick) * tick


def floor_2dec(x: float) -> float:
    return int(x * 100) / 100.0


# ──────────────────────────────────────────────────────────────────────────
# Trader
# ──────────────────────────────────────────────────────────────────────────


class Trader:
    """
    Owns: target_buy_accumulator, PositionTracker.
    Pipeline: handle_fill() → consume_chunk → translate → place_order → track.
    """

    BUFFER_CAP_MULTIPLIER = 3   # max buffer size = threshold × this (protects against runaway accumulation on repeated POST failures)

    def __init__(self, config: dict, clob: ClobClient, state: dict):
        self.config = config
        self.clob = clob
        # Per-asset buffer of target's BUY shares; reset to 0 after each copy
        self.target_buy_accumulator: dict[str, float] = state.get("target_buy_accumulator", {})
        # Open positions (will be GC'd after endDate + buffer)
        self.positions: list[PositionEntry] = [
            PositionEntry(**p) for p in state.get("positions", [])
        ]
        self._state_dirty = False
        # Background tasks (Gamma endDate fetches) — held to prevent GC and
        # cancelled cleanly on shutdown.
        self._bg_tasks: set[asyncio.Task] = set()

    # ── State serialization ──

    def export_state(self) -> dict:
        return {
            "target_buy_accumulator": self.target_buy_accumulator,
            "positions": [asdict(p) for p in self.positions],
        }

    @property
    def dirty(self) -> bool:
        return self._state_dirty

    def mark_clean(self) -> None:
        self._state_dirty = False

    # ── Headroom + expiry ──

    def current_total_open_usd(self, now_ms: int) -> float:
        return sum(p.cost_basis_usd for p in self.positions if not self._is_expired(p, now_ms))

    def _is_expired(self, p: PositionEntry, now_ms: int) -> bool:
        if p.end_date_ms is not None:
            return now_ms > p.end_date_ms + self.config["position_expiry"]["buffer_s"] * 1000
        return (now_ms - p.opened_at_ms) > self.config["position_expiry"]["fallback_ttl_min"] * 60_000

    def gc_expired(self, now_ms: int) -> int:
        """Drop expired positions from tracker; return count dropped."""
        before = len(self.positions)
        kept = []
        for p in self.positions:
            if self._is_expired(p, now_ms):
                end_info = f"endDate+{self.config['position_expiry']['buffer_s']}s passed" \
                    if p.end_date_ms is not None else "fallback_ttl_min reached"
                log.info(
                    f"[EXPIRE] position asset={p.asset_id[:12]}… "
                    f"cost=${p.cost_basis_usd:.2f} → drop ({end_info})"
                )
                # Also clear accumulator for this asset (rebuild from scratch if it returns)
                self.target_buy_accumulator.pop(p.asset_id, None)
                self._state_dirty = True
            else:
                kept.append(p)
        self.positions = kept
        return before - len(kept)

    # ── Batching accumulator ──

    def stage_chunk_if_ready(self, target_fill: TargetFill) -> Optional[float]:
        """
        Always commits the new fill into the buffer (bounded by BUFFER_CAP).
        Returns chunk_shares if buffer has crossed threshold — but does NOT
        reset. Caller must call commit_copied_chunk() after a successful POST
        /order to reset the buffer; if POST fails, buffer stays so the next
        fill keeps building. Buffer is capped at threshold×BUFFER_CAP_MULTIPLIER
        to prevent runaway accumulation after repeated POST failures.
        """
        asset = target_fill.asset
        threshold = self.config["sizing"]["min_target_shares_to_copy"]
        max_buffer = threshold * self.BUFFER_CAP_MULTIPLIER
        new_acc = self.target_buy_accumulator.get(asset, 0.0) + target_fill.size
        if new_acc > max_buffer:
            log.warning(
                f"[BUFFER-CAP] asset={asset[:12]}… buffer would be {new_acc:.2f}, "
                f"capping at {max_buffer:.2f} (threshold×{self.BUFFER_CAP_MULTIPLIER})"
            )
            new_acc = max_buffer
        self.target_buy_accumulator[asset] = new_acc
        self._state_dirty = True

        if new_acc < threshold:
            log.info(
                f"[SKIP] accumulating_below_threshold asset={asset[:12]}… "
                f"buffer={new_acc:.2f} threshold={threshold}"
            )
            return None

        log.info(
            f"[CHUNK] asset={asset[:12]}… chunk={new_acc:.2f} shares "
            f"(threshold {threshold} crossed — pending POST result)"
        )
        return new_acc

    def commit_copied_chunk(self, asset: str) -> None:
        """Called after a successful POST /order — reset buffer to 0 for that asset."""
        if asset in self.target_buy_accumulator:
            self.target_buy_accumulator[asset] = 0.0
            self._state_dirty = True

    # ── Sizing ──

    def _size_fixed(self, target_fill: TargetFill, chunk_shares: float, total_open: float) -> Optional[float]:
        usd = self.config["sizing"]["fixed_usd_per_fill"]
        headroom = self.config["sizing"]["max_usd_total_in_positions"] - total_open
        if headroom <= 0:
            return None
        return min(usd, headroom)

    def _size_percent_of_target(self, target_fill: TargetFill, chunk_shares: float, total_open: float) -> Optional[float]:
        chunk_usd = chunk_shares * target_fill.price
        usd = chunk_usd * self.config["sizing"]["percent_of_target"]
        headroom = self.config["sizing"]["max_usd_total_in_positions"] - total_open
        if headroom <= 0:
            return None
        return min(usd, headroom)

    def _compute_size_usd(self, target_fill: TargetFill, chunk_shares: float, total_open: float) -> Optional[float]:
        mode = self.config["sizing"]["mode"]
        if mode == "fixed":
            return self._size_fixed(target_fill, chunk_shares, total_open)
        if mode == "percent_of_target":
            return self._size_percent_of_target(target_fill, chunk_shares, total_open)
        raise ValueError(f"unknown sizing mode: {mode}")

    # ── Translator ──

    def _translate(self, target_fill: TargetFill, chunk_shares: float, total_open: float) -> Optional[OrderSpec]:
        # Bot only buys
        if target_fill.side != "BUY":
            return None

        usd = self._compute_size_usd(target_fill, chunk_shares, total_open)
        if usd is None:
            log.info(f"[SKIP] headroom_exhausted total_open=${total_open:.2f} cap=${self.config['sizing']['max_usd_total_in_positions']:.2f}")
            return None

        # Taker: limit = target_price * (1 + slippage_bps/10000)
        # Maker: limit = target_price + offset_ticks * tick (forced below best_ask via book check is skipped — we don't query book)
        order_type_cfg = self.config["execution"]["order_type"]
        tick = infer_tick_from_price(target_fill.price_str)

        if order_type_cfg == "taker":
            slippage_bps = self.config["slippage"]["entry_bps_max"]
            limit_price = target_fill.price * (1 + slippage_bps / 10000)
            order_type = "FAK"
        elif order_type_cfg == "maker":
            offset_ticks = self.config["maker_settings"]["price_offset_ticks"]
            limit_price = target_fill.price + offset_ticks * tick
            order_type = "GTC"
        else:
            raise ValueError(f"unknown order_type: {order_type_cfg}")

        my_limit_price = round_to_tick(limit_price, tick)
        if my_limit_price <= 0:
            log.warning(f"[SKIP] non_positive_price computed_limit={my_limit_price}")
            return None
        # PM binary outcomes: hard-cap at (1 - tick) per inferred tick.
        max_price = TICK_MAX_PRICE.get(tick, 1.0 - tick)
        if my_limit_price > max_price:
            log.info(
                f"[CAP] limit_price {my_limit_price:.4f} > {max_price:.4f} "
                f"(max for tick={tick}) → capped"
            )
            my_limit_price = max_price

        # USD → shares
        shares = floor_2dec(usd / my_limit_price)

        # CLOB minimum bump
        if shares < CLOB_MIN_SHARES:
            five_cost = CLOB_MIN_SHARES * my_limit_price
            headroom = self.config["sizing"]["max_usd_total_in_positions"] - total_open
            if five_cost > headroom:
                log.info(
                    f"[SKIP] insufficient_headroom_for_5_shares "
                    f"headroom=${headroom:.2f} need=${five_cost:.2f}"
                )
                return None
            log.info(f"[BUMP] desired={shares:.2f} < 5 → using 5 shares (cost ${five_cost:.2f})")
            shares = CLOB_MIN_SHARES

        return OrderSpec(
            asset_id=target_fill.asset,
            side="BUY",
            size=shares,
            price=my_limit_price,
            order_type=order_type,
            market_slug=target_fill.market_slug,
            target_price=target_fill.price,
        )

    # ── Main entry: handle one fill ──

    async def handle_fill(self, target_fill: TargetFill) -> None:
        """Process one new target fill: batch → translate → place → track."""
        if target_fill.side != "BUY":
            log.info(f"[SKIP] target_sell_ignored asset={target_fill.asset[:12]}… size={target_fill.size:.2f}")
            return

        chunk_shares = self.stage_chunk_if_ready(target_fill)
        if chunk_shares is None:
            return

        now_ms = int(time.time() * 1000)
        self.gc_expired(now_ms)
        total_open = self.current_total_open_usd(now_ms)

        spec = self._translate(target_fill, chunk_shares, total_open)
        if spec is None:
            return

        t_pre_post = int(time.time() * 1000)
        result = await self.clob.place_order(spec)
        t_post_done = int(time.time() * 1000)

        if not result.success:
            # POST failed — buffer keeps the chunk; next fill keeps building
            # from the same baseline so we retry on the next fill that arrives.
            return

        # POST succeeded — commit the buffer reset for this asset.
        self.commit_copied_chunk(spec.asset_id)

        # Single consolidated log line — replaces clob.py's [COPY]/[DRY-RUN] +
        # the previous separate [LATENCY] line.
        tag = "DRY-RUN" if result.dry_run else "COPY"
        usd = spec.size * spec.price
        order_id_short = (result.order_id[:10] + "…") if result.order_id else "?"
        if target_fill.timestamp_ms > 0:
            detect = t_pre_post - target_fill.timestamp_ms
            rtt = t_post_done - t_pre_post
            total = t_post_done - target_fill.timestamp_ms
            lat_str = f" lat={total}ms(pre={detect} rtt={rtt})"
        else:
            lat_str = ""
        log.info(
            f"[{tag}] BUY {spec.size:.2f}@{spec.price:.4f} type={spec.order_type} "
            f"usd=${usd:.2f} asset={spec.asset_id[:12]}… order={order_id_short}{lat_str}"
        )

        # Cost basis for BUY: USDC paid = makingAmount (taker side is shares,
        # NOT USDC). Falls back to spec.size * spec.price in dry_run.
        if not result.dry_run and result.making_amount_usdc > 0:
            cost_basis = result.making_amount_usdc
        else:
            cost_basis = spec.size * spec.price
        entry = PositionEntry(
            asset_id=spec.asset_id,
            market_slug=spec.market_slug,
            cost_basis_usd=cost_basis,
            opened_at_ms=now_ms,
            end_date_ms=None,
            order_id=result.order_id,
        )
        self.positions.append(entry)
        self._state_dirty = True

        # Async fetch endDate (don't block). Hold reference so Python's
        # GC doesn't collect mid-execution (3.11+ docs requirement).
        t = asyncio.create_task(self._enrich_with_end_date(entry))
        self._bg_tasks.add(t)
        t.add_done_callback(self._bg_tasks.discard)

    async def _enrich_with_end_date(self, entry: PositionEntry) -> None:
        try:
            end_ms = await self.clob.fetch_market_end_date(entry.market_slug)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning(f"[EXPIRY-FALLBACK] slug={entry.market_slug} Gamma error: {e}")
            return
        if end_ms is None:
            log.warning(
                f"[EXPIRY-FALLBACK] slug={entry.market_slug} Gamma failed → "
                f"using fallback_ttl_min={self.config['position_expiry']['fallback_ttl_min']}min"
            )
            return
        entry.end_date_ms = end_ms
        self._state_dirty = True
        log.info(
            f"[GAMMA] slug={entry.market_slug} endDate={end_ms} "
            f"(in {(end_ms - int(time.time() * 1000)) / 1000:.0f}s)"
        )

    async def cancel_bg_tasks(self) -> None:
        """Cancel any in-flight Gamma fetches — call before closing aiohttp session."""
        for t in list(self._bg_tasks):
            t.cancel()
        if self._bg_tasks:
            await asyncio.gather(*self._bg_tasks, return_exceptions=True)
