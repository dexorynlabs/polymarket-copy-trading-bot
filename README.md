# Polymarket Bot | Polymarket Trading Bot | Polymarket Copy Trading Bot  

**Languages:** [English](README.md) · [中文](public/README.zh-CN.md) · [Русский](public/README.ru.md)

> **Automated Polymarket copy trading bot that mirrors active traders in real time**  
> **Predictions & Perps • Multi-wallet • Web dashboard • Live tested • Real on-chain execution**

> **Need help or an updated build?**  
> 📱 **Telegram**: [t.me/dexoryn](https://t.me/dexoryn) | 🎮 **Discord**: `dexoryn_`

---

## 🎥 Live Profit Videos (Historical - Gabagool22)

These sessions were recorded while **@gabagool22** was actively trading. They show the bot executing real copy trades on-chain-not a simulation.

**Wallet (historical target):** `0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d`

> **Note:** Gabagool22 is no longer a reliable copy target. The videos remain proof that the bot worked in production; add **active wallets** as targets in the dashboard (or `targets.yaml`). See [Story 3](#story-3--bot-still-running-after-gabagool22-stopped) below.

### Video 1 - Live Copy Trading Run

https://github.com/user-attachments/assets/2194ef92-b0f7-40e1-9835-4d2965e85e81

- **+$80 profit in ~15 minutes**
- Bot ran unattended during this session
- Real on-chain execution, not simulation

### Video 2 - Second run (confirmation)

https://github.com/user-attachments/assets/df3a6791-89b5-4230-ae40-fb7130dcadc4

- **Additional +$230 profit in the next ~15 minutes**
- Same bot, same logic, separate run
- Fully automated copy trading

---

## 📖 Live Test Stories (Real Usage)

### Story 1 - Unattended session (Gabagool22 era)

After updating the bot, I ran it to test the new logic and left it running while I went out to play billiards with friends.

About one hour later, when I returned:

- ✅ The bot was running normally
- ✅ It was copy trading accurately
- ✅ Trades matched the target trader's transactions
- ✅ The bot had already generated profit

This was a fully unattended live run, not a simulation or backtest.

---

### Story 2 - Repeatable performance (video runs)

The two videos above are from **separate live sessions** on different days. Same codebase, same monitoring and execution pipeline-no manual clicking through Polymarket. That repeatability is what we optimize for: stable automation, not a one-off lucky trade.

---

### Story 3 - Bot still running after Gabagool22 stopped

<a id="story-3--bot-still-running-after-gabagool22-stopped"></a>

Gabagool22 eventually **slowed down and stopped being a practical copy target**-fewer trades, different behavior, or simply going inactive. A lot of copy traders hit the same wall: the wallet that worked last month goes quiet, and their bot looks "broken" when the real issue is an **empty signal**, not broken software.

What we did:

- Kept the **same bot** running-no rewrite, no new product
- Added **new active wallets** as targets in the dashboard (saved to `targets.yaml`)
- Confirmed the full pipeline still works: trade detection → sizing → order posting → logging

What we saw:

- ✅ Process stayed up and healthy
- ✅ New target trades were detected and mirrored correctly
- ✅ Activity history and `state.json` updated as expected
- ✅ Failures were isolated to market/order edge cases, not "bot died when Gabagool22 left"

#### Perfect copy-trading result - mirroring **securebet**

After switching targets, we copied [**securebet**](https://polymarket.com/@securebet) and captured this side-by-side:

<p align="center">
  <img src="public/Realtradehistory/securebet.jpg" alt="Copy trading PnL: bot wallet vs securebet target - matching chart shape" width="100%"/>
</p>

**This is what ideal copy trading looks like.** Your bot wallet (left) and the target trader (right) show the **same PnL chart shape** for the day-the same flat period, dip, and recovery spike at the end. Dollar amounts differ because of your sizing settings and balance, but the **curve tracks the leader**, which means trades are being detected and mirrored in sync-not lagging behind or fighting the strategy.

Same session, same markets in the activity/history tabs (e.g. the temperature markets visible in the screenshot). That alignment is the proof traders care about: **follow the wallet, get the same equity curve pattern.**

**Takeaway for traders:** This bot is built to follow **whoever you configure**, not one celebrity wallet. When a trader stops working for you, **change the target-not the bot.** Past Gabagool22 results do not guarantee future results on any target.

---

## 🆕 What's new

Multi-wallet copy, web dashboard (`http://127.0.0.1:8787`), Polymarket Perps, lower-latency WebSocket path, optional exit mirroring (`copy_closes`), and Telegram alerts. The videos above are from **predictions**-start in `dry_run`, confirm **Activity**, then switch to `real`.

---

## ⭐ Why This Bot

Live **video proof** and real stories-not screenshots. WebSocket detection, per-target sizing caps, share batching, dry-run mode, and a dashboard to swap targets when a leader goes quiet (see Story 3).

| | This Bot | Typical alternatives |
|---|----------|----------------------|
| Live proof | ✅ Videos + stories | ❌ Claims only |
| Multi-wallet + dashboard | ✅ | ❌ Single address / CLI |
| Perps + exit mirroring | ✅ | ❌ Predictions / entry only |
| Survives inactive target | ✅ Swap in UI | ⚠️ Tied to one wallet |

**Good fit:** passive copy traders comfortable with Python 3.10+, on-chain risk, and monitoring **Activity**. **Not a fit:** guaranteed profits, simultaneous predictions + perps, or a public dashboard without `web.token`.

---

**Jump to:** [Quick Start](#-quick-start) · [Configuration](#configuration) · [FAQ](#faq)

## 🚀 Quick Start

**Needs:** Python 3.10+, Polygon wallet + CLOB API (for `real` predictions), funded Perps account (for `real` perps). Node.js 18+ only if you rebuild the UI.

```bash
git clone https://github.com/dexorynlabs/polymarket-trading-bot-python.git
cd polymarket-trading-bot-python
pip install -r requirements.txt
cp config.yaml.example config.yaml   # mode, web, polymarket secrets
python -m app.main
```

1. Keep **`mode: dry_run`** until fills show in dashboard **Activity**
2. Open **http://127.0.0.1:8787** → **Targets** → add wallet, venue (`predictions` | `perps`), sizing → **Start**
3. Switch to **`mode: real`**, restart, and start again with small size

**Dashboard:** Overview, Targets, Activity, Positions, Settings (writes to `targets.yaml` / `settings.yaml`). Set `web.token` before exposing beyond localhost.

**Perps:** set target `venue: perps`, fund on [polymarket.com](https://polymarket.com). One venue copies at a time-predictions **or** perps, not both.

UI rebuild (optional): `cd ui && npm install && npm run build` · see [`ui/README.md`](ui/README.md)

**Help:** [@dexoryn](https://t.me/dexoryn)

---

## Configuration

Secrets and global mode in **`config.yaml`**. Targets and tuning in the **dashboard** (or `targets.yaml` / `settings.yaml`). Dashboard overrides matching config keys.

| Key | Purpose |
|-----|---------|
| `mode` | `dry_run` or `real` |
| `copy.venue` | `predictions` or `perps` |
| `web.*` | Dashboard host, port, optional token |
| `risk.max_open_usd_total` | Optional cap across prediction targets |
| `execution.order_type` | `taker` (FAK) or `maker` (GTC) |
| `slippage.entry_bps_max` | Max BUY slippage (bps) |

For `mode: real`, fill `polymarket:` credentials. Per-target fields: `wallet`, `venue`, `enabled`, `copy_closes`, `sizing.*`. Legacy single `target_wallet` configs auto-migrate on first launch. Full reference: **`config.yaml.example`**.

Pick active traders on [polymarket.com](https://polymarket.com) and rotate when activity drops.

---

## Safety

⚠️ **`mode: real` uses real funds.** Start dry-run, use a limited wallet, set per-target caps, check `logs/copybot.log` and **Activity**, never commit secrets. Past results do not guarantee future returns.

---

## FAQ

**Multiple wallets?** Yes on predictions (parallel, per-target caps). One venue active at a time.

**Target stopped trading?** Bot keeps running-no new copies until you enable an active target.

**Still need `config.yaml`?** Yes for mode, API secrets, web/Telegram. Targets live in the dashboard.

**Logs?** `logs/copybot.log`, `history.db`, `state.json`, `settings.yaml`.

---

## Author & Contact

**Dexoryn Labs** · [@dexoryn](https://t.me/dexoryn) · Discord `dexoryn_` · [@dexoryn](https://x.com/dexoryn) · [@dexorynLabs](https://github.com/dexorynLabs)

<p align="center">
  <img src="public/dexoryn_tg.jpg" alt="Telegram QR - @dexoryn" height="220"/>
  &nbsp;&nbsp;
  <img src="public/dexoryn_wechat.png" alt="WeChat QR - DexorynWe" height="220"/>
</p>

---

## Contributing

Fork → branch → PR. Dev: `pip install -r requirements-dev.txt` && `pytest`.

---

## Legal Disclaimer

Trading on Polymarket involves **substantial risk of loss**. Dexoryn is not responsible for losses from using this software. **Only trade with funds you can afford to lose.**

Questions: [@dexoryn](https://t.me/dexoryn) · ⭐ star the repo if it helps.
