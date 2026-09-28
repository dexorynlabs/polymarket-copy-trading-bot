# Polymarket 机器人 | Polymarket 交易机器人 | Polymarket 跟单机器人

**语言：** [English](../README.md) · [中文](README.zh-CN.md) · [Русский](README.ru.md)

> **实时镜像活跃交易者的 Polymarket 自动跟单机器人**  
> **预测市场 & 永续 • 多钱包 • Web 仪表盘 • 实盘验证 • 真实链上执行**

> **需要帮助或更新版本？**  
> 📱 **Telegram**：[t.me/dexoryn](https://t.me/dexoryn) | 🎮 **Discord**：`dexoryn_`

---

## 🎥 实盘盈利视频（历史记录 - Gabagool22）

这些录像拍摄于 **@gabagool22** 仍活跃交易期间，展示机器人在链上执行真实跟单，而非模拟。

**钱包（历史跟单目标）：** `0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d`

> **说明：** Gabagool22 已不再是可靠的跟单对象。视频仍可证明机器人曾在生产环境正常运行；在仪表盘（或 `targets.yaml`）中添加**当前仍活跃**的钱包作为目标。见下方 [故事 3](#story-3--bot-still-running-after-gabagool22-stopped)。

### 视频 1 - 实盘跟单运行

https://github.com/user-attachments/assets/2194ef92-b0f7-40e1-9835-4d2965e85e81

- **约 15 分钟内 +$80 盈利**
- 本次会话全程无人值守
- 真实链上执行，非模拟

### 视频 2 - 第二次运行（验证）

https://github.com/user-attachments/assets/df3a6791-89b5-4230-ae40-fb7130dcadc4

- **随后约 15 分钟再 +$230**
- 同一机器人、同一逻辑、独立运行
- 全自动跟单

---

## 📖 实盘故事（真实使用）

### 故事 1 - 无人值守会话（Gabagool22 时期）

更新机器人逻辑后，我启动测试并出门和朋友打台球，机器人持续运行。

约一小时后返回：

- ✅ 机器人运行正常
- ✅ 跟单准确
- ✅ 成交与目标交易者一致
- ✅ 已产生盈利

这是完全无人值守的实盘运行，不是模拟或回测。

---

### 故事 2 - 可重复的表现（视频运行）

上方两段视频来自**不同日期**的两次实盘会话。同一套代码、同一监控与执行流水线--无需在 Polymarket 上手动点击。我们追求的是**稳定自动化**，而非单次运气。

---

### 故事 3 - Gabagool22 停更后机器人仍正常运行

<a id="story-3--bot-still-running-after-gabagool22-stopped"></a>

Gabagool22 最终**交易减少，不再适合作为跟单目标**--成交变少、策略变化或已不再活跃。很多跟单者会遇到同样问题：上个月好用的钱包安静下来，机器人看起来像「坏了」，但真正原因往往是**没有信号**，而不是软件故障。

我们做了什么：

- **同一套机器人**继续运行--无需重写或换产品
- 在仪表盘中添加**新的活跃钱包**作为目标（保存至 `targets.yaml`）
- 确认完整流程仍正常：检测交易 → 计算仓位 → 下单 → 日志记录

我们观察到：

- ✅ 进程稳定健康
- ✅ 新目标的交易被正确检测并镜像
- ✅ 活动历史与 `state.json` 按预期更新
- ✅ 失败仅出现在个别市场/订单边界情况，而非「Gabagool22 一走机器人就挂了」

#### 完美跟单结果 - 镜像 **securebet**

更换目标后，我们跟单 [**securebet**](https://polymarket.com/@securebet)，并拍下这张对比图：

<p align="center">
  <img src="Realtradehistory/securebet.jpg" alt="跟单盈亏：机器人钱包 vs securebet 目标 - 曲线形状一致" width="100%"/>
</p>

**这就是理想跟单应有的样子。** 左侧为你的机器人钱包，右侧为目标交易者，当日 **盈亏曲线形状一致**--相同的横盘、回撤与末尾反弹。美元金额因你的仓位设置与余额而不同，但**曲线跟随领头钱包**，说明交易被及时检测并同步镜像，而非滞后或偏离策略。

同一时段、活动/历史标签页中的市场也一致（例如截图中的温度类市场）。这种对齐才是交易者真正关心的证明：**跟随钱包，获得相同的权益曲线形态。**

**给交易者的结论：** 本机器人跟单**你配置的任何地址**，而非绑定某个「明星钱包」。当某位交易者不再适合你时，**换地址，不要换机器人。** Gabagool22 的过往表现不保证任何目标未来的结果。

---

## 🆕 本版本新功能

多钱包跟单、Web 仪表盘（`http://127.0.0.1:8787`）、Polymarket 永续、WebSocket 低延迟路径、可选退出镜像（`copy_closes`）与 Telegram 提醒。上方视频来自**预测市场**--请先在 `dry_run` 下确认 **活动**，再切换 `real`。

---

## ⭐ 为什么选择本机器人

**实盘视频**与真实故事，而非截图。WebSocket 检测、按目标 sizing、份额批处理、模拟模式，以及领头停更时在仪表盘换目标（见故事 3）。

| | 本机器人 | 常见替代 |
|---|----------|----------|
| 实盘证明 | ✅ 视频 + 故事 | ❌ 仅宣传 |
| 多钱包 + 仪表盘 | ✅ | ❌ 单地址 / CLI |
| 永续 + 退出镜像 | ✅ | ❌ 仅预测 / 仅入场 |
| 目标停更后仍可用 | ✅ UI 换目标 | ⚠️ 绑定单一钱包 |

**适合：** 能运行 Python 3.10+、理解链上风险、会查看 **活动** 的被动跟单者。**不适合：** 保证盈利、同时跟单预测+永续、或未设 `web.token` 就公开仪表盘。

---

**跳转：** [快速开始](#-快速开始) · [配置](#配置) · [常见问题](#常见问题)

## 🚀 快速开始

**需要：** Python 3.10+、Polygon 钱包 + CLOB API（`real` 预测）、已充值永续账户（`real` 永续）。仅重建 UI 时需要 Node.js 18+。

```bash
git clone https://github.com/dexorynlabs/polymarket-trading-bot-python.git
cd polymarket-trading-bot-python
pip install -r requirements.txt
cp config.yaml.example config.yaml   # mode、web、polymarket 密钥
python -m app.main
```

1. 保持 **`mode: dry_run`**，直到 **活动** 中出现成交
2. 打开 **http://127.0.0.1:8787** → **目标** → 添加钱包、venue（`predictions` | `perps`）、sizing → **Start**
3. 确认无误后设 **`mode: real`**，重启，小仓位再次 Start

**仪表盘：** 概览、目标、活动、持仓、设置（写入 `targets.yaml` / `settings.yaml`）。暴露到 localhost 外请先设 `web.token`。

**永续：** 目标 `venue: perps`，在 [polymarket.com](https://polymarket.com) 充值。同一时间仅一个 venue--预测或永续。

UI 重建（可选）：`cd ui && npm install && npm run build` · 见 [`ui/README.md`](../ui/README.md)

**帮助：** Telegram [@dexoryn](https://t.me/dexoryn)

---

## 配置

密钥与全局 mode 在 **`config.yaml`**。目标与调参在**仪表盘**（或 `targets.yaml` / `settings.yaml`）。仪表盘会覆盖对应 config 项。

| 键 | 用途 |
|----|------|
| `mode` | `dry_run` 或 `real` |
| `copy.venue` | `predictions` 或 `perps` |
| `web.*` | 仪表盘 host、port、可选 token |
| `risk.max_open_usd_total` | 预测目标总敞口上限（可选） |
| `execution.order_type` | `taker`（FAK）或 `maker`（GTC） |
| `slippage.entry_bps_max` | BUY 最大滑点（bps） |

`mode: real` 时填写 `polymarket:` 凭证。每目标：`wallet`、`venue`、`enabled`、`copy_closes`、`sizing.*`。旧版单 `target_wallet` 首次启动自动迁移。完整说明见 **`config.yaml.example`**。

在 [polymarket.com](https://polymarket.com) 选择活跃交易者，活跃度下降时轮换。

---

## 安全

⚠️ **`mode: real` 使用真实资金。** 先 dry-run、专用小余额钱包、设单目标上限、查看 `logs/copybot.log` 与 **活动**，切勿提交密钥。过往结果不保证未来收益。

---

## 常见问题

**多个钱包？** 预测 venue 可并行，各有上限。同一时间仅一个 venue 活跃。

**目标停止交易？** 机器人继续运行，启用新目标前无新跟单。

**还需要 `config.yaml`？** 需要 mode、API 密钥、web/Telegram。目标在仪表盘中管理。

**日志？** `logs/copybot.log`、`history.db`、`state.json`、`settings.yaml`。

---

## 作者与联系

**Dexoryn Labs** · [@dexoryn](https://t.me/dexoryn) · Discord `dexoryn_` · [@dexoryn](https://x.com/dexoryn) · [@dexorynLabs](https://github.com/dexorynLabs)

<p align="center">
  <img src="dexoryn_tg.jpg" alt="Telegram 二维码 - @dexoryn" height="220"/>
  &nbsp;&nbsp;
  <img src="dexoryn_wechat.png" alt="微信二维码 - DexorynWe" height="220"/>
</p>

---

## 贡献

Fork → 分支 → PR。开发：`pip install -r requirements-dev.txt` && `pytest`。

---

## 法律声明

在 Polymarket 交易存在**重大亏损风险**。Dexoryn 不对使用本软件造成的损失负责。**请仅使用您能承受损失的资金。**

问题咨询：Telegram [@dexoryn](https://t.me/dexoryn) · 有帮助请 ⭐ Star。
