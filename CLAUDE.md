# UZI-Skill (US edition) · Claude Code Context

> Auto-read by Claude Code to provide project context.

## What this is

A US-stock deep-analysis plugin. When the user says "analyze TICKER", you should
trigger the `deep-analysis` skill. **US-listed equities only** — A-share / Hong
Kong tickers and Chinese company names are rejected up front with a clear message.
All output is in English.

## Core skills

| Skill | Trigger | Notes |
|---|---|---|
| `deep-analysis` | "analyze / research / value / DCF / is it worth buying" | 15 data dims + 35-investor jury + Bloomberg report |
| `investor-panel` | "just show the jury / what would the legends think" | Run the investor panel on its own |

## Workflow · two depths

**Fast path (default):** when the user says "analyze / take a look", run the CLI directly.
```
python3 run.py <TICKER> --depth lite --no-browser   # 30-60s
python3 run.py <TICKER> --depth medium --no-browser # 2-4min, default completeness
```
If `agent_analysis.json` is missing, the CLI degrades to a warning and still emits the
HTML report. **No need to role-play the 35 jurors.**

**Deep path:** only when the user explicitly wants DCF / IC memo / initiation /
investment-committee deliverables, use the two-stage flow:
1. `stage1()` — script collects data + rule-engine skeleton scores
2. **You step in** — read `panel.json`, role-play the 35 jurors, write `agent_analysis.json`
3. `stage2()` — merges your analysis and generates the report

See `AGENTS.md` / `skills/deep-analysis/SKILL.md` for the full flow.

## Key files

- `AGENTS.md` — full agent instructions
- `skills/deep-analysis/SKILL.md` — deep-analysis workflow
- `skills/deep-analysis/scripts/run_real_test.py` — main engine
- `commands/analyze-stock.md` — the `/analyze-stock` command
