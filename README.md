<div align="center">

# UZI Skills — US Edition

*"A jury of legendary investors reviews your stock picks — Buffett, Munger, Lynch, Wood, Burry and more, all at one table."*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.com/product/claude-code)
[![Dimensions](https://img.shields.io/badge/Dimensions-15-brightgreen)]()
[![Investors](https://img.shields.io/badge/Investors-35-orange)]()
[![Market](https://img.shields.io/badge/Market-US%20only-red)]()

**US-stock deep-analysis engine** · 15 data dimensions × a 35-investor jury × institutional methods (DCF / Comps / LBO) · Bloomberg-style HTML report.

</div>

---

> **US edition.** This is a fork of [wbh604/UZI-Skill](https://github.com/wbh604/UZI-Skill) retargeted to **US-listed equities only**, with an **English-only** interface and output. The China A-share / Hong Kong markets, the Dragon-Tiger-List (龙虎榜) and "youzi" day-trader tooling, and the Chinese-market investor personas have been removed. Enter a US ticker (e.g. `AAPL`); A-share/HK tickers are rejected with a clear message.

## What it does

Give it a US ticker and Claude becomes your analyst — it pulls **15 dimensions of data**, runs institutional models, has **35 investors with distinct methodologies** score the stock, and produces a self-contained Bloomberg-style HTML report.

```
/stock-deep-analyzer:analyze-stock AAPL     # Apple
/stock-deep-analyzer:analyze-stock MSFT     # Microsoft
/stock-deep-analyzer:analyze-stock NVDA     # Nvidia
/stock-deep-analyzer:analyze-stock BRK.B    # Berkshire Hathaway
```

After a few minutes you get:
- **A self-contained HTML report** — opens in any browser, works offline
- **A portrait share card** (1080×1920) for social media
- **A landscape "war report" card** (1920×1080)
- **A one-line summary** for chat / Slack

## Install

### Claude Code

```
/plugin marketplace add wbh604/UZI-Skill
/plugin install stock-deep-analyzer@uzi-skill
```

Then say `/stock-deep-analyzer:analyze-stock AAPL`.

> ⚠️ Always use the `stock-deep-analyzer:` namespace prefix — short names (`/analyze-stock`) don't resolve in every environment.

### CLI (git clone)

```bash
git clone https://github.com/wbh604/UZI-Skill.git && cd UZI-Skill
pip install -r requirements.txt
python run.py AAPL
```

## Usage

### Full deep analysis

```
/stock-deep-analyzer:analyze-stock AAPL
```

### Focused commands

> All commands take a US ticker. Prefix with `/stock-deep-analyzer:`.

| Command | What it does |
|---|---|
| `/stock-deep-analyzer:dcf AAPL` | DCF valuation · WACC + 5×5 sensitivity table |
| `/stock-deep-analyzer:comps MSFT` | Comparable-company analysis · P/E, P/B percentiles |
| `/stock-deep-analyzer:lbo AAPL` | LBO test · what IRR a PE buyer could earn |
| `/stock-deep-analyzer:initiate NVDA` | Institutional initiation report · JPM/GS format |
| `/stock-deep-analyzer:ic-memo AAPL` | Investment-committee memo · three-scenario returns |
| `/stock-deep-analyzer:earnings AAPL` | Earnings read · beat/miss detection |
| `/stock-deep-analyzer:earnings-preview AAPL` | Pre-earnings preview · consensus + Bull/Base/Bear |
| `/stock-deep-analyzer:catalysts AAPL` | Catalyst calendar · next 60 days |
| `/stock-deep-analyzer:thesis AAPL` | Thesis tracker · five-pillar monitoring |
| `/stock-deep-analyzer:screen AAPL` | Quant screens · value / growth / quality |
| `/stock-deep-analyzer:dd AAPL` | Due-diligence checklist · 5 workflows |
| `/stock-deep-analyzer:quick-scan AAPL` | 30-second read |
| `/stock-deep-analyzer:panel-only AAPL` | Just the 35-investor jury vote |
| `/stock-deep-analyzer:segmental-model AAPL` | Segment-level bottom-up model · 3 scenarios × 3 years |
| `/stock-deep-analyzer:ai-readiness NVDA` | AI-readiness / bottleneck assessment |
| `/stock-deep-analyzer:model-update AAPL` | Incremental model update after new results/guidance |
| `/stock-deep-analyzer:returns` | Portfolio return attribution |
| `/stock-deep-analyzer:rebalance` | Per-holding rebalance · drift + trade list |

### CLI power usage (git clone)

```bash
python run.py AAPL --depth lite --no-browser   # 30-60s quick mode
python run.py NVDA --school I                   # lock to one school's lens (A/B/C/D/G/H/I)
python run.py --versus AAPL MSFT                # 2-4 tickers head-to-head · ★WIN highlight
python run.py --portfolio holdings.csv          # CSV portfolio · weighted score + health
python run.py AAPL --output-dir /tmp/out         # SaaS integration · index.html + meta.json
```

## The 35-investor jury

Seven schools of distinct methodologies score every stock and the report surfaces where they disagree:

- **A · Classic Value** — Buffett, Graham, Fisher, Munger, Templeton, Klarman
- **B · Growth** — Lynch, O'Neil, Thiel, Wood, Andreessen, Gurley, Naval, Gerstner, Chamath
- **C · Macro / Hedge** — Soros, Dalio, Marks, Druckenmiller, Robertson, Burry, Chanos
- **D · Technical / Trend** — Livermore, Minervini, Darvas, Gann
- **G · Quant** — Simons, Thorp, Shaw, Asness
- **H · Tech Leaders** — Jensen Huang, Musk, Altman, Saylor
- **I · AI Bottleneck Hunter** — Serenity

## Data sources

The data layer is provider-based with automatic failover (`akshare`, `yfinance`, `baostock`). `yfinance` provides US-native coverage with zero API keys. See [docs/DATA-PROVIDERS.md](docs/DATA-PROVIDERS.md).

## Disclaimer

This tool is for research and educational purposes only. Nothing it produces is investment advice. Markets carry risk; do your own diligence.

## License

MIT — see [LICENSE](LICENSE). Upstream project: [wbh604/UZI-Skill](https://github.com/wbh604/UZI-Skill).
