# UZI-Skill (US edition) · Gemini CLI instructions

## Install

```bash
gemini extensions install https://github.com/wbh604/UZI-Skill
```

Update:

```bash
gemini extensions update stock-deep-analyzer
```

## Usage

Tell Gemini "analyze AAPL", or run directly:

```bash
pip install -r requirements.txt
python run.py AAPL --no-browser
```

US-listed tickers only.

## Full flow

See `AGENTS.md` and `skills/deep-analysis/SKILL.md`.

The core is a two-stage flow:
1. `stage1()` — data collection + rule-engine skeleton scores
2. Agent analysis — read panel.json, role-play the 35 jurors group by group
3. `stage2()` — generate the Bloomberg-style HTML report
