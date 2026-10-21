# CoinWatch

[![CI](https://github.com/AlfredoJamesPacino/coinwatch/actions/workflows/ci.yml/badge.svg)](https://github.com/AlfredoJamesPacino/coinwatch/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

**本地优先的加密货币行情监控与告警引擎。**

多数据源自动故障切换，标准库零依赖，调度无关（cron / Windows 任务计划 / WorkBuddy 自动化都能驱动）。

> CoinWatch 只做**数据监控与告警**，不提供任何投资建议。加密货币市场高风险，请自行判断。

---

## 为什么要有它

盯盘的实际痛点，其实就三个：

1. **单一数据源不可靠** —— CoinGecko 免费额度会限流，Binance 在某些地区被墙，OKX 偶尔抖动。挂了就什么都看不到。
2. **不想一直开着交易所 App** —— 只想在该动的时候被叫一声。
3. **担心凭证乱飞** —— 没人希望自己的密钥躺在某个不知名软件的数据库里。

CoinWatch 的设计回答就是：**多源兜底 + 阈值告警 + 完全不需要交易所密钥**（只用公开行情接口）。

---

## 特性

- 🔁 **多源故障切换**：CoinGecko → Binance → OKX 逐级兜底，按币种补齐，单源挂掉不影响整体
- 🔔 **多类告警**：24h 涨跌幅、上下方价格突破、成交量异动（滚动基线）
- 📡 **多渠道通知**：终端日志 / Telegram / Discord / Email(SMTP)
- 🌐 **本地面板**：内置 Web Dashboard（每 60s 自动刷新），只监听 `127.0.0.1`
- 📦 **零第三方依赖**：核心只用 Python 标准库，克隆下来就能跑
- 🕒 **调度无关**：不自带定时器，交给 cron / 任务计划 / WorkBuddy
- 🧩 **易扩展**：新增数据源只需实现 `Source.fetch()`

---

## 快速开始

要求 **Python 3.11+**（用到标准库 `tomllib`）。

```bash
git clone https://github.com/AlfredoJamesPacino/coinwatch.git
cd coinwatch

# 安装（可选；不装也能跑）
pip install -e .

# 生成配置
coinwatch init          # 从 config.example.toml 复制出 config.toml
# 编辑 config.toml，设置自选币种、阈值、通知渠道

# 跑一次
coinwatch check
```

不想安装的话，直接用模块方式运行：

```bash
PYTHONPATH=src python -m coinwatch.cli check
PowerShell:  $env:PYTHONPATH="src"; python -m coinwatch.cli check
```

首屏输出类似：

```
=== CoinWatch 行情快照 ===

SYMBOL           PRICE        24H   SOURCE
----------------------------------------------
BTC         $67,432.10    +2.31%   coingecko
ETH          $3,210.55    -1.04%   binance
SOL            $178.22    +6.77%   coingecko

无告警。
```

---

## 配置

编辑 `config.toml`（**该文件已被 `.gitignore` 忽略，别提交**）：

```toml
[watchlist]
bitcoin  = "BTC"     # 左边是 CoinGecko coin id（小写）
ethereum = "ETH"
solana   = "SOL"

[thresholds]
change_pct_alert = 5.0                        # |24h 涨跌| >= 5% 就告警，0 关闭
volume_spike_pct = 0.0                        # 成交量异动阈值，0 关闭
price_above = { "bitcoin" = 200000 }          # 突破上方
price_below = { "ethereum" = 500 }            # 跌破下方

[notify]
log = true
telegram_token = ""          # 从 @BotFather 拿
telegram_chat_id = ""
discord_webhook = ""
email_smtp_host = ""         # 留空即关闭邮件通道
email_smtp_user = ""
email_smtp_pass = ""         # 建议用应用专用密码
email_to = ""
```

**安全注意**： bot token 和 SMTP 密码只存在本地 `config.toml` 里，**从不随代码提交**。仓库只提交脱敏的 `config.example.toml`。

---

## 命令

| 命令 | 作用 |
| --- | --- |
| `coinwatch check` | 拉一次快照，评估阈值，有告警就推送 |
| `coinwatch list` | 只列出自选行情，不触发告警 |
| `coinwatch watch [--interval N]` | 循环监控，默认读配置里的 `interval_seconds` |
| `coinwatch web` | 启动本地面板，默认 `http://127.0.0.1:8080` |
| `coinwatch init` | 从示例生成 `config.toml` |

所有命令都支持 `--config <path>` 指定配置文件位置。

---

## 网络与区域可用性

CoinWatch 只用公开行情接口，但这些接口在**部分地区/网络下可能直连不通**（Binance、OKX、CoinGecko 均有被拦或限流的情况）。

遇到这种情况时，CoinWatch **不会假装没数据**，而会把失败原因打出来：

```
行情源不可用：
  ! coingecko: https://api.coingecko.com/... -> Tunnel connection failed: 502 Bad Gateway
  ! binance:   https://api.binance.com/...   -> Tunnel connection failed: 502 Bad Gateway
  -> 常见原因：本机网络到该 API 不通（部分地区需代理）、或被限流。
```

处理方式：给本机配好代理即可，`urllib` 会自动读取 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
coinwatch check
```

由于 3 个源会互相兜底，即使只有一个能通，快照依然完整。

---

## 定时执行

CoinWatch **不自带守护进程**，这是刻意的——交给更专业的调度器，也更省资源。

**Linux / macOS（cron，每 5 分钟）：**

```cron
*/5 * * * * cd /path/to/coinwatch && python -m coinwatch.cli check >> coinwatch.log 2>&1
```

**Windows（任务计划程序）：**

```powershell
$action  = New-ScheduledTaskAction -Execute "python" `
           -Argument "-m coinwatch.cli check" -WorkingDirectory "C:\path\to\coinwatch"
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)
Register-ScheduledTask -TaskName "CoinWatch" -Action $action -Trigger $trigger
```

**WorkBuddy 自动化：** 创建一条定时任务，指令为「运行 `coinwatch check` 」，即可把告警接进 AI 工作流。

---

## 架构

```
src/coinwatch/
├── config.py      # TOML 加载与阈值访问
├── market.py      # Market：多源聚合 + 按币种 failover
├── alert.py       # 阈值评估，成交量基线持久化
├── notifier.py    # log / Telegram / Discord / Email
├── report.py      # 文本 & JSON 渲染
├── web.py         # 标准库 http.server 面板
├── cli.py         # argparse 入口
└── sources/
    ├── base.py       # Quote / Source 抽象
    ├── coingecko.py
    ├── binance.py
    └── okx.py
```

数据流：

```
config.toml → Market.snapshot() → alert.evaluate() → notifier.notify()
                     ↑
        CoinGecko → Binance → OKX（逐级兜底）
```

**新增一个数据源**：继承 `Source`，实现 `fetch(coin_ids, symbols) -> dict[str, Quote]`，然后丢进 `Market(sources=[...])`。解析逻辑请配一个 `monkeypatch` 单测，参考 `tests/test_sources.py`。

---

## 开发

```bash
pip install -e ".[dev]"
pytest -q
```

测试不访问网络——用 `monkeypatch` 打桩 `_get_json` 来验证解析逻辑，所以 CI 里跑得又快又稳。

---

## 免责声明

本项目**仅用于行情监控与告警**，不提供任何投资建议、买卖信号或收益承诺。所有数据来自第三方公开 API，可能延迟或不准确，请以交易所实际成交为准。加密货币市场波动剧烈、风险极高，请自行判断并控制风险。

---

## License

[MIT](LICENSE) © 2026 MT
