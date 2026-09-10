"""app-tracecopy — Polymarket copy-trader entrypoint.

Loads config, validates, wires Poller + Trader + ClobClient, runs asyncio loop.

Run either way:
  python -m app.main           # canonical (from project root)
  python app/main.py           # also works (path-bootstrapped below)
"""

import sys
from pathlib import Path

# Bootstrap: if launched as `python app/main.py`, the project root isn't on
# sys.path so `from app.* import ...` would fail. Insert parent dir explicitly.
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import asyncio
import contextlib
import json
import logging
import os
import re
import signal
from pathlib import Path

import aiohttp
import yaml

from app.core.poller import Poller
from app.core.trader import Trader
from app.pm.clob import ClobClient


CONFIG_FILE = "config.yaml"
STATE_FILE = "state.json"
LOG_FILE = "logs/tracecopy.log"
SAVE_INTERVAL_S = 5.0

WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


# ──────────────────────────────────────────────────────────────────────────
# Config validation
# ──────────────────────────────────────────────────────────────────────────


class ConfigError(Exception):
    pass


def _require(d: dict, path: str):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise ConfigError(f"missing required config: {path}")
        cur = cur[part]
    return cur


def validate_config(cfg: dict) -> None:
    # Non-secret required fields
    target = _require(cfg, "target_wallet")
    if not WALLET_RE.match(target):
        raise ConfigError(f"target_wallet must match 0x[hex]{{40}}, got {target!r}")

    mode = _require(cfg, "mode")
    if mode not in ("dry_run", "real"):
        raise ConfigError(f"mode must be dry_run|real, got {mode!r}")

    sm = _require(cfg, "sizing.mode")
    if sm not in ("fixed", "percent_of_target"):
        raise ConfigError(f"sizing.mode must be fixed|percent_of_target, got {sm!r}")

    if _require(cfg, "sizing.fixed_usd_per_fill") <= 0:
        raise ConfigError("sizing.fixed_usd_per_fill must be > 0")
    pct = _require(cfg, "sizing.percent_of_target")
    if not (0 < pct <= 1):
        raise ConfigError("sizing.percent_of_target must be in (0, 1]")
    cap = _require(cfg, "sizing.max_usd_total_in_positions")
    if cap <= 5.0:
        raise ConfigError("sizing.max_usd_total_in_positions must be > 5.0")
    if _require(cfg, "sizing.min_target_shares_to_copy") < 5:
        raise ConfigError("sizing.min_target_shares_to_copy must be >= 5")

    ot = _require(cfg, "execution.order_type")
    if ot not in ("taker", "maker"):
        raise ConfigError(f"execution.order_type must be taker|maker, got {ot!r}")

    bps = _require(cfg, "slippage.entry_bps_max")
    if not (0 < bps < 10000):
        raise ConfigError("slippage.entry_bps_max must be in (0, 10000)")

    _require(cfg, "position_expiry.buffer_s")
    if _require(cfg, "position_expiry.fallback_ttl_min") < 5:
        raise ConfigError("position_expiry.fallback_ttl_min must be >= 5")

    if _require(cfg, "dedup.seen_cap") < 1000:
        raise ConfigError("dedup.seen_cap must be >= 1000")

    if _require(cfg, "watchdog.max_consecutive_errors") < 1:
        raise ConfigError("watchdog.max_consecutive_errors must be >= 1")
    if _require(cfg, "watchdog.silent_timeout_s") < 10:
        raise ConfigError("watchdog.silent_timeout_s must be >= 10")

    # Secrets validation
    if mode == "real":
        secrets = cfg.get("polymarket")
        if not secrets:
            raise ConfigError("mode=real requires polymarket: section")
        missing = [
            k for k in ("private_key", "wallet_address", "api_key", "api_secret", "passphrase")
            if not secrets.get(k)
        ]
        if missing:
            raise ConfigError(f"mode=real missing polymarket fields: {missing}")


# ──────────────────────────────────────────────────────────────────────────
# State
# ──────────────────────────────────────────────────────────────────────────


def load_state() -> dict:
    p = Path(STATE_FILE)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception as e:
        log = logging.getLogger("main")
        log.warning(f"Failed to load {STATE_FILE}: {e} — starting fresh")
        return {}


def save_state(poller: Poller, trader: Trader) -> None:
    state = {
        **poller.export_state(),
        **trader.export_state(),
    }
    tmp = Path(STATE_FILE).with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


async def state_saver(poller: Poller, trader: Trader, shutdown: asyncio.Event) -> None:
    # `save_state` does JSON serialization + atomic file replace. With large
    # seen_tx_keys (50k+) it can spend 50-100ms — push to a thread so the
    # WS receive loop doesn't stall.
    while not shutdown.is_set():
        try:
            await asyncio.wait_for(shutdown.wait(), timeout=SAVE_INTERVAL_S)
            break
        except asyncio.TimeoutError:
            pass
        if poller.dirty or trader.dirty:
            await asyncio.to_thread(save_state, poller, trader)
            poller.mark_clean()
            trader.mark_clean()
    # Final save on shutdown
    await asyncio.to_thread(save_state, poller, trader)


async def gc_loop(trader: Trader, shutdown: asyncio.Event) -> None:
    """Periodically drop expired positions from tracker."""
    import time
    while not shutdown.is_set():
        try:
            await asyncio.wait_for(shutdown.wait(), timeout=30)
            return
        except asyncio.TimeoutError:
            pass
        trader.gc_expired(int(time.time() * 1000))


# ──────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────


def setup_logging() -> None:
    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)-5s %(name)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    handlers: list[logging.Handler] = []
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    handlers.append(sh)
    Path("logs").mkdir(exist_ok=True)
    fh = logging.FileHandler(LOG_FILE)
    fh.setFormatter(fmt)
    handlers.append(fh)
    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)


async def amain() -> int:
    setup_logging()
    log = logging.getLogger("main")

    if not os.path.exists(CONFIG_FILE):
        log.error(f"{CONFIG_FILE} not found — copy config.yaml.example and edit")
        return 2

    with open(CONFIG_FILE) as f:
        cfg = yaml.safe_load(f)

    try:
        validate_config(cfg)
    except ConfigError as e:
        log.error(f"Config invalid: {e}")
        return 2

    mode = cfg["mode"]
    log.info("=" * 60)
    log.info(f"app-tracecopy starting — mode={mode.upper()}")
    log.info(f"  target_wallet:  {cfg['target_wallet']}")
    log.info(f"  data source:    WebSocket wss://ws-live-data.polymarket.com")
    log.info(f"  sizing.mode:    {cfg['sizing']['mode']}")
    if cfg["sizing"]["mode"] == "fixed":
        log.info(f"  fixed_usd:      ${cfg['sizing']['fixed_usd_per_fill']:.2f} per copy")
    else:
        log.info(f"  percent_target: {cfg['sizing']['percent_of_target'] * 100:.1f}% of chunk")
    log.info(f"  max_total_usd:  ${cfg['sizing']['max_usd_total_in_positions']:.2f}")
    log.info(f"  min_target_sh:  {cfg['sizing']['min_target_shares_to_copy']} shares (batching)")
    log.info(f"  order_type:     {cfg['execution']['order_type']}")
    log.info(f"  slippage_bps:   {cfg['slippage']['entry_bps_max']}")
    log.info("=" * 60)

    state = load_state()

    timeout = aiohttp.ClientTimeout(total=10, connect=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        clob = ClobClient(secrets=cfg.get("polymarket"), dry_run=(mode == "dry_run"), session=session)

        trader = Trader(cfg, clob, state)
        poller = Poller(cfg, session, trader.handle_fill, state)

        shutdown = asyncio.Event()

        def handle_sig(signum):
            log.info(f"signal {signum} received, shutting down")
            shutdown.set()

        loop = asyncio.get_running_loop()
        for s in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(s, handle_sig, s)
            except NotImplementedError:
                pass

        tasks = [
            asyncio.create_task(poller.run(shutdown), name="poller"),
            asyncio.create_task(poller.silent_watchdog(shutdown), name="watchdog"),
            asyncio.create_task(state_saver(poller, trader, shutdown), name="state_saver"),
            asyncio.create_task(gc_loop(trader, shutdown), name="gc_loop"),
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        # If any task crashed, signal others to shut down
        shutdown.set()
        for t in pending:
            t.cancel()
        # Wait for cancelled tasks to actually finish before closing the session
        for t in pending:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await t
        # Cancel orphan trader bg tasks (in-flight Gamma /markets fetches)
        await trader.cancel_bg_tasks()
        for t in done:
            if t.exception() is not None:
                log.exception(f"task {t.get_name()} raised", exc_info=t.exception())

    log.info("Shutdown complete")
    return 0


def main() -> int:
    try:
        return asyncio.run(amain())
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
