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

本仓库是**生产级跟单机器人**，而非单钱包脚本：

- **多钱包跟单** - 添加、启用或暂停多个目标；每个目标独立 sizing 与敞口上限
- **更低延迟路径** - WebSocket 检测、有界成交队列、CLOB 连接保活
- **Web 仪表盘** - 在浏览器中管理目标、查看活动、持仓与设置
- **Polymarket 永续** - 从领头账户复制永续合约组合（与预测市场为不同 venue）
- **退出镜像** - 可选按比例复制 SELL / 平仓（`copy_closes`）
- **Telegram 提醒** - 跟单成功、失败与错误可选推送

上方视频来自**预测市场**流水线。永续与仪表盘为较新功能--请先在 `dry_run` 下运行，在 UI 中确认活动后再切换 `real`。

---

## ⭐ 为什么选择本机器人

### 🎯 真实证明，而非空口宣传

许多 Polymarket 机器人只有截图。本仓库提供**实盘视频**与上述故事--包括在明星交易者停更后**仍能正常运行**。

### 🚀 架构与性能

- **WebSocket 成交流** - 订阅 Polymarket 实时 activity 流，快速检测
- **非阻塞流水线** - 有界成交队列，下单不会阻塞 WS 循环
- **CLOB 保活** - HTTP 连接池在跟单订单之间保持热连接
- **按目标独立组合** - 每个钱包独立的 sizing、去重与敞口跟踪
- **SQLite 历史** - `history.db` 驱动活动流与事后复盘
- **设置覆盖** - 仪表盘修改持久化到 `settings.yaml`，无需重启

### 💡 交易者真正会用到的功能

- **多目标管理** - 同时跟单多个预测或永续领头（预测 venue）
- **Web 仪表盘** - 概览、目标、活动、持仓、设置，默认 `http://127.0.0.1:8787`
- **预测 + 永续** - 在仪表盘中切换 copy venue（同一时间仅一个活跃 venue）
- **复制平仓** - 镜像目标退出，而非仅入场
- **份额批处理** - 累积小单后再提交（有助于最小单与 gas）
- **固定或比例仓位** - 按目标设置 USD 或 leader chunk 比例
- **模拟模式** - `config.yaml` 中 `mode: dry_run` 仅记录意图
- **Taker / Maker** - FAK 吃单（含滑点上限）或 GTC 挂单
- **Telegram 通知** - 跟单事件与错误可选推送
- **连接看门狗** - WS 僵尸连接时重连或退出，便于干净重启

### 📈 对比

| 功能 | 本机器人 | 常见替代方案 |
|------|----------|--------------|
| **实盘执行证明** | ✅ 视频 + 真实故事 | ❌ 仅宣传 |
| **多钱包跟单** | ✅ 按目标上限 | ❌ 单地址 |
| **Web 仪表盘** | ✅ 内置 | ❌ 仅 CLI / `.env` |
| **永续跟单** | ✅ | ❌ 仅预测市场 |
| **退出镜像** | ✅ 可选 | ❌ 仅入场 |
| **延迟可视化** | ✅ 仪表盘图表 | ❌ |
| **目标停更后仍可用** | ✅ UI 换目标 | ⚠️ 绑定单一 KOL |
| **WebSocket 检测** | ✅ | ⚠️ 仅轮询 |
| **模拟模式** | ✅ | ❌ |
| **份额批处理** | ✅ | ❌ |
| **持久化状态** | ✅ `state.json` + history DB | ⚠️ 有限 |

---

## 🎯 适合谁

**适合：**

- 希望**被动跟随**信任钱包的交易者
- 偏好**仪表盘**而非每次改 YAML 的用户
- 跟单**多个领头**或在活跃度下降时轮换目标的人
- 能运行 **Python 3.10+** 并维护本地进程的用户
- 理解**链上风险**、gas，以及领头者会随时间变化的人

**不适合：**

- 期望**保证盈利**或永远无需盯盘的「印钞机」心态
- 需要**同时**跟单预测市场与永续（复制时仅一个 venue 活跃）
- 在未设置 `web.token` 的情况下将仪表盘暴露到公网
- 完全不查看日志或活动流的新手

---

**跳转：** [快速开始](#-快速开始) · [仪表盘](#-仪表盘) · [永续](#-永续跟单) · [配置](#配置) · [贡献](#贡献)

## 🚀 快速开始

### 环境要求

- **Python 3.10+**
- **Node.js 18+**（仅在你自行构建仪表盘 UI 时需要）
- **Polygon 钱包** - 预测市场用 USDC，gas 用 POL/MATIC（`mode: real` 时）
- **Polymarket CLOB API 凭证** - 预测市场实盘下单所需
- **已充值的永续账户** - 仅在 `real` 模式下跟单 Polymarket 永续时需要

## 安装

```bash
git clone https://github.com/dexorynlabs/polymarket-trading-bot-python.git
cd polymarket-trading-bot-python

pip install -r requirements.txt

cp config.yaml.example config.yaml
# 编辑 config.yaml - mode、web 设置、polymarket 密钥（real 模式）

python -m app.main
```

### 首次运行（推荐）

1. 保持 **`mode: dry_run`**，直到在仪表盘 **活动** 标签页看到目标成交
2. 打开 **http://127.0.0.1:8787**（默认 `web.host` / `web.port`）
3. 在 **目标** 页添加钱包地址、venue（`predictions` 或 `perps`）、sizing
4. 在要复制的 venue 上点击 **Start**
5. 行为确认无误后，设置 **`mode: real`**，重启，并以小仓位再次 Start

从源码构建 UI（可选；生产构建输出到 `app/web/static/`）：

```bash
cd ui
npm install
npm run build
```

详见 [`ui/README.md`](../ui/README.md) 中的 `dev`、`dev:mock` 与认证说明。

**帮助：** Telegram [@dexoryn](https://t.me/dexoryn)

---

## 🖥 仪表盘

内置仪表盘是首次 `config.yaml` 配置后的主要操作界面。

| 页面 | 用途 |
|------|------|
| **概览** | 跟单状态、活跃 venue、延迟快照 |
| **目标** | 添加、编辑、启用或暂停领头钱包 |
| **活动** | 检测到的成交与跟单结果实时流 |
| **持仓** | 当前敞口与剩余额度 |
| **设置** | sizing、滑点、通知；保存至 `settings.yaml` |

默认地址：**http://127.0.0.1:8787**

> 除非设置了 `web.token`，请保持 `web.host: 127.0.0.1`。请勿在未认证的情况下将仪表盘公开到互联网。

若 UI 要求 token，在 `config.yaml` 中设置 `web.token`，并在设置页输入相同值。

---

## 📈 永续跟单

从目标账户复制 **Polymarket 永续** 持仓：

- 通过轮询目标公开永续资料检测组合变化
- 订单为 mark ± 配置滑点的 IOC 限价单
- 在仪表盘或 `targets.yaml` 中将目标 `venue` 设为 `perps`
- **`copy.venue: perps`** 在选择 Start 时启用永续流水线
- 委托签名会话保存在 `perps_session.json`（已 gitignore）
- 实盘跟单前请在 [polymarket.com](https://polymarket.com) 为永续账户充值

**同一时间仅一个 venue：** 跟单时**预测市场**或**永续**二选一，不能同时运行。需要切换时在仪表盘中更换 venue。

---

## 配置

在 **`config.yaml`** 中配置密钥与全局 mode。目标与大部分调参在**仪表盘**中完成（持久化至 `targets.yaml` 与 `settings.yaml`）。

请从 `mode: dry_run` 开始。仪表盘对交易设置的修改会覆盖 `config.yaml` 中的对应项。

### `config.yaml` 核心设置

| 设置 | 说明 | 示例 |
|------|------|------|
| `mode` | `dry_run` 记录/模拟；`real` 提交订单 | `dry_run` |
| `copy.venue` | 开始跟单时的初始 venue | `predictions` |
| `web.enabled` | 启用仪表盘 | `true` |
| `web.host` / `web.port` | 绑定地址 | `127.0.0.1` / `8787` |
| `web.token` | 可选 API/仪表盘认证 | `""` |
| `risk.max_open_usd_total` | 可选：所有预测目标总敞口上限 | `null` |
| `execution.order_type` | `taker`（FAK）或 `maker`（GTC） | `taker` |
| `slippage.entry_bps_max` | BUY 跟单最大滑点（bps） | `1000` |
| `perps.poll_interval_s` | 永续组合轮询间隔 | `1.0` |
| `telegram.enabled` | Telegram 推送 | `false` |

`mode: real` 时填写 `polymarket:` 下的 `private_key`、`wallet_address`、`api_key`、`api_secret`、`passphrase`。Maker 设置、最小单、去重、看门狗等见 **`config.yaml.example`**。

### 目标（`targets.yaml` / 仪表盘）

首次运行时，`config.yaml` 中的目标会种子化 `targets.yaml`。之后请在 **目标** 页管理。

| 字段 | 说明 |
|------|------|
| `name` | 仪表盘显示名称 |
| `venue` | `predictions`（CLOB）或 `perps` |
| `wallet` | 领头 proxy 钱包（预测）或账户地址（永续） |
| `enabled` | 暂停而不删除 |
| `copy_closes` | 镜像目标 SELL / 减仓 |
| `sizing.mode` | 预测：`fixed` 或 `percent_of_target`；永续：`percent_of_target` 或 `fixed_notional` |
| `sizing.max_open_usd` / `max_open_notional_usd` | 单目标敞口上限 |

旧版仅含 `target_wallet` 与顶层 `sizing:` 的配置会在首次启动时**自动迁移**为单一目标。

### 选择跟单目标

在 [polymarket.com](https://polymarket.com) 核实活跃度与风险后再启用目标。活跃度下降时轮换领头--Gabagool22 是教训，不是永久设置。

---

## 安全与风险管理

⚠️ **`mode: real` 时本机器人使用真实资金进行真实交易。**

- 先用 `mode: dry_run`，并在 **活动** 中确认成交
- 交易者不活跃时**更换目标**
- 设置保守的单目标上限与可选 `risk.max_open_usd_total`
- 定期查看 `logs/copybot.log` 与仪表盘 **活动** 标签
- 过往表现（含视频）**不保证**未来结果

1. 使用余额有限的专用钱包  
2. 切勿提交含 live 密钥的 `config.yaml`、`targets.yaml` 或 `settings.yaml`  
3. 若仪表盘可被 localhost 以外访问，请设置 `web.token`  
4. 知道如何停止机器人（`Ctrl+C`）并在仪表盘中暂停跟单  
5. 添加目标前做好研究  

---

## 常见问题

**可以同时跟单多个钱包吗？**  
可以，在**预测** venue 下--多个已启用目标并行跟单，各有 sizing 上限。永续可配置多个目标；但同一时间仅一个 **venue**（预测或永续）在复制。

**可以同时跟单预测市场与永续吗？**  
不可以。在仪表盘中切换 venue，以保持保证金与风险逻辑清晰。

**还能跟单 Gabagool22 吗？**  
可以设置任意地址，但 Gabagool22 **已不再推荐**--活跃度下降。请选择**当前活跃**的交易者。

**如果目标停止交易怎么办？**  
机器人会继续运行；启用活跃目标前不会有新跟单。这是正常现象，不是故障。

**用了仪表盘还需要 `config.yaml` 吗？**  
需要，用于 `mode`、API 密钥与 web/Telegram 设置。日常目标编辑在仪表盘 / `targets.yaml` 中完成。

**日志与历史存在哪里？**  
`logs/copybot.log`、`history.db`、`state.json`、`settings.yaml`（均已 gitignore，示例配置除外）。

**支持所有 Polymarket 市场吗？**  
支持标准市场；冷门或边界情况可能单笔失败并记录。

**是否开源？**  
是。另有维护中的高级版本，可通过 Telegram 获取额外支持。

---

## 作者与联系

**Dexoryn Labs** - Polymarket 跟单自动化

- **Telegram**：[@dexoryn](https://t.me/dexoryn)（回复最快）
- **Discord**：`dexoryn_`
- **Twitter**：[@dexoryn](https://x.com/dexoryn)
- **GitHub**：[@dexorynLabs](https://github.com/dexorynLabs)
- **微信**：扫码添加 **DexorynWe**

<p align="center">
  <img src="dexoryn_tg.jpg" alt="Telegram 二维码 - @dexoryn" height="280"/>
  &nbsp;&nbsp;
  <img src="dexoryn_wechat.png" alt="微信二维码 - 扫码添加 DexorynWe 为好友" height="280"/>
</p>

---

## 贡献

1. Fork 本仓库  
2. `git checkout -b feature/your-feature`  
3. 提交并推送  
4. 发起 Pull Request  

开发依赖：`pip install -r requirements-dev.txt`，然后 `pytest`。

---

## 法律声明

在 Polymarket 交易存在**重大亏损风险**。Dexoryn 不对使用本软件造成的损失负责。钱包安全、目标选择与资金风险由您自行承担。

**请仅使用您能承受损失的资金进行交易。**

---

若本项目对您有帮助，欢迎 ⭐ Star 本仓库或提交 Issue/PR。问题咨询：Telegram [@dexoryn](https://t.me/dexoryn)。
