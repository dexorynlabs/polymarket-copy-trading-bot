# Polymarket 机器人 | Polymarket 交易机器人 | Polymarket 跟单机器人

**语言：** [English](README.md) · [中文](README.zh-CN.md) · [Русский](README.ru.md)

> **实时镜像活跃交易者的 Polymarket 自动跟单机器人**  
> **实盘验证 • 真实链上执行 • 随时更换跟单目标**

> **需要帮助或更新版本？**  
> 📱 **Telegram**：[t.me/dexoryn](https://t.me/dexoryn) | 🎮 **Discord**：`dexoryn_`

---

## 🎥 实盘盈利视频（历史记录 - Gabagool22）

这些录像拍摄于 **@gabagool22** 仍活跃交易期间，展示机器人在链上执行真实跟单，而非模拟。

**钱包（历史跟单目标）：** `0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d`

> **说明：** Gabagool22 已不再是可靠的跟单对象。视频仍可证明机器人曾在生产环境正常运行；请在 `config.yaml` 中将 `target_wallet` 指向**当前仍活跃**的交易者。见下方 [故事 3](#story-3--bot-still-running-after-gabagool22-stopped)。

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
- 在 `config.yaml` 中将 `target_wallet` 更新为**其他活跃的 Polymarket 钱包**
- 确认完整流程仍正常：检测交易 → 计算仓位 → 下单 → 日志记录

我们观察到：

- ✅ 进程稳定健康
- ✅ 新目标的交易被正确检测并镜像
- ✅ 日志与 `state.json` 按预期更新
- ✅ 失败仅出现在个别市场/订单边界情况，而非「Gabagool22 一走机器人就挂了」

#### 完美跟单结果 - 镜像 **securebet**

更换目标后，我们跟单 [**securebet**](https://polymarket.com/@securebet)，并拍下这张对比图：

<p align="center">
  <img src="Realtradehistory/securebet.jpg" alt="跟单盈亏：机器人钱包 vs securebet 目标 - 曲线形状一致" width="100%"/>
</p>

**这就是理想跟单应有的样子。** 左侧为你的机器人钱包，右侧为目标交易者，当日 **盈亏曲线形状一致**--相同的横盘、回撤与末尾反弹。美元金额因你的仓位设置与余额而不同，但**曲线跟随领头钱包**，说明交易被及时检测并同步镜像，而非滞后或偏离策略。

**给交易者的结论：** 本机器人跟单**你配置的任何地址**，而非绑定某个「明星钱包」。当某位交易者不再适合你时，**换地址，不要换机器人。** Gabagool22 的过往表现不保证任何目标未来的结果。

---

## ⭐ 为什么选择本机器人

### 🎯 真实证明，而非空口宣传

许多 Polymarket 机器人只有截图。本仓库提供**实盘视频**与上述故事--包括在明星交易者停更后**仍能正常运行**。

### 🚀 架构与性能

- **WebSocket 成交流** - 订阅 Polymarket 实时 activity 流，低延迟检测
- **异步优先** - 基于 Python `asyncio`，有界队列避免下单阻塞 WS 循环
- **持久化状态** - 去重键与持仓写入 `state.json`

### 💡 交易者真正会用到的功能

- **份额批处理** - 累积目标小单至阈值后一次性跟单
- **固定或比例仓位** - `fixed` 固定 USD 或 `percent_of_target` 按比例
- **模拟模式** - `mode: dry_run` 仅记录意图，不下单
- **Taker / Maker** - FAK 吃单（含滑点上限）或 GTC 挂单
- **总仓位上限** - `max_usd_total_in_positions` 全局限制
- **连接看门狗** - WS 静默超时自动退出，便于进程管理器重启

---

## 🎯 适合谁

**适合：**

- 希望**被动跟随**信任钱包的交易者
- 能运行 **Python 3.10+** 并编辑 `config.yaml` 的用户
- 理解**链上风险**、gas，以及领头者会随时间变化的人

**不适合：**

- 期望**保证盈利**或永远无需盯盘的「印钞机」心态
- 完全不查看日志、不在活跃度下降时更换目标的新手

---

**跳转：** [快速开始](#快速开始) · [安装](#安装) · [配置](#配置) · [贡献](#贡献)

## 快速开始

### 环境要求

- **Python 3.10+**
- **Polygon 钱包** - 交易用 USDC，gas 用 POL/MATIC（`mode: real` 时）
- **Polymarket CLOB API 凭证** - 实盘下单所需

### 安装

```bash
git clone https://github.com/dexorynlabs/polymarket-copy-trading-bot.git
cd polymarket-copy-trading-bot

pip install -r requirements.txt

cp config.yaml.example config.yaml
# 编辑 config.yaml - 设置 target_wallet 和 mode（见下方配置说明）
python -m app.main
```

**帮助：** Telegram [@dexoryn](https://t.me/dexoryn)

---

## 配置

编辑项目根目录的 `config.yaml`。先用 `mode: dry_run` 确认机器人能检测并记录目标成交，再切换实盘。

### 核心设置

| 设置 | 说明 | 示例 |
|------|------|------|
| `target_wallet` | 要跟单的 Polymarket 钱包 | `0x6031b6e...` |
| `mode` | `dry_run` 仅记录；`real` 提交订单 | `dry_run` |
| `sizing.mode` | `fixed` 固定 USD 或 `percent_of_target` 按比例 | `fixed` |
| `sizing.fixed_usd_per_fill` | 每次跟单 USD（`sizing.mode=fixed` 时） | `10.0` |
| `sizing.percent_of_target` | 目标 chunk 比例（`percent_of_target` 时） | `0.05` |
| `sizing.max_usd_total_in_positions` | 持仓成本全局上限 | `100.0` |
| `sizing.min_target_shares_to_copy` | 批处理阈值（份额） | `10` |
| `execution.order_type` | `taker`（FAK）或 `maker`（GTC） | `taker` |
| `slippage.entry_bps_max` | 相对目标价最大滑点（bps） | `200` |

`mode: real` 时，取消注释并填写 `polymarket:` 下的 `private_key`、`wallet_address`、`api_key`、`api_secret`、`passphrase`。Maker 设置、持仓过期、去重与看门狗见 **`config.yaml`**。

### 选择跟单目标

在 [polymarket.com](https://polymarket.com) 核实活跃度与风险后，将活跃钱包地址写入 `target_wallet`。

---

## 安全与风险管理

⚠️ **`mode: real` 时本机器人使用真实资金进行真实交易。**

- 先用 `mode: dry_run` 确认日志中的跟单意图
- 交易者不活跃时**更换 `target_wallet`**
- 保守设置 `sizing.max_usd_total_in_positions`
- 定期查看 `logs/tracecopy.log`；状态保存在 `state.json`
- 过往表现（含视频）**不保证**未来结果

1. 使用余额有限的专用钱包  
2. 切勿提交含密钥的 `config.yaml` 或泄露 `private_key`  
3. 知道如何停止机器人（`Ctrl+C`）  
4. 设置 `target_wallet` 前做好研究  

---

## 常见问题

**还能跟单 Gabagool22 吗？**  
可以设置任意地址，但 Gabagool22 **已不再推荐**--活跃度下降。请选择**当前活跃**的交易者。

**如果目标停止交易怎么办？**  
机器人会继续运行；将 `target_wallet` 指向活跃钱包前不会有新跟单。这是正常现象，不是机器人故障。

**支持所有 Polymarket 市场吗？**  
支持标准市场；冷门或流动性差的情况可能单笔失败并记录。

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

---

## 法律声明

在 Polymarket 交易存在**重大亏损风险**。Dexoryn 不对使用本软件造成的损失负责。钱包安全、目标选择与资金风险由您自行承担。

**请仅使用您能承受损失的资金进行交易。**

---

若本项目对您有帮助，欢迎 ⭐ Star 本仓库或提交 Issue/PR。问题咨询：Telegram [@dexoryn](https://t.me/dexoryn)。
