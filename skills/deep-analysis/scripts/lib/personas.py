"""v2.15.0 · YAML persona 加载 + prefix-stable system message 构建（借鉴 augur 设计）.

设计原则：
- Persona YAML 是 Rules 引擎的补充，不是替代 —— Rules 仍给确定性骨架分
- agent role-play 阶段读取 persona，让 headline / commentary 更 in-voice
- flagship persona（12 手写）优先级 > stub persona（39 自动生成）
- stub persona 存在是为了让 51 人名单完整，但 agent 应主要靠 Rules 判断
- prefix-stable system message：所有 51 persona 调用共用同一 system prompt，利用 prompt cache
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PERSONAS_DIR = Path(__file__).resolve().parent.parent.parent / "personas"


@dataclass
class Persona:
    id: str
    name: str
    school: str
    group: str  # A-G
    philosophy: str = ""
    key_metrics: list[str] = field(default_factory=list)
    avoids: list[str] = field(default_factory=list)
    a_share_view: str = ""
    voice: str = ""
    famous_positions: list[str] = field(default_factory=list)
    is_flagship: bool = False  # flagship 手写 vs stub 自动生成
    raw: dict = field(default_factory=dict)

    def to_prompt_block(self) -> str:
        """把 persona 压缩为 LLM system prompt 里的段落（< 600 字）."""
        lines = [
            f"# PERSONA · {self.name} ({self.id})",
            f"School: {self.school} · Group: {self.group}",
            "",
        ]
        if self.philosophy:
            lines.append(f"## Philosophy\n{self.philosophy.strip()[:400]}")
        if self.key_metrics:
            lines.append(f"\n## Key Metrics / Signals\n" + "\n".join(f"- {m}" for m in self.key_metrics[:8]))
        if self.avoids:
            lines.append(f"\n## Avoids\n" + "\n".join(f"- {a}" for a in self.avoids[:6]))
        # US edition: the China-specific `a_share_view` field is no longer rendered.
        if self.voice:
            lines.append(f"\n## Voice / Tone\n{self.voice.strip()[:200]}")
        if self.famous_positions:
            lines.append(f"\n## Famous Positions\n" + "\n".join(f"- {p}" for p in self.famous_positions[:5]))
        return "\n".join(lines)


def _parse_minimal_yaml(text: str) -> dict:
    """零依赖迷你 YAML parser · 只处理 personas/ 下的简化格式.

    支持：
    - `key: value` 标量
    - `key: |` 多行字符串
    - `key:` 后跟 `  - item` 列表
    - `# comment` 注释
    - 顶级 key: dict（比如 _meta: { key: val, key: val }）
    """
    result: dict[str, Any] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        # 顶级 key · 必须顶格（没 leading space）
        if not line.startswith(" ") and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value == "|":
                # 多行字符串（下面带缩进的都归这个 key）
                block = []
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if not nxt.strip() and (i + 1 >= len(lines) or not lines[i+1].startswith(" ")):
                        break
                    if nxt.startswith("  "):
                        block.append(nxt[2:] if nxt.startswith("  ") else nxt)
                        i += 1
                    elif not nxt.strip():
                        block.append("")
                        i += 1
                    else:
                        break
                result[key] = "\n".join(block).rstrip()
                continue
            elif value == "":
                # 要么是列表，要么是嵌套 dict
                items = []
                child = {}
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if nxt.startswith("  - "):
                        items.append(nxt[4:].strip())
                        i += 1
                    elif nxt.startswith("  ") and ":" in nxt and not nxt.startswith("    "):
                        sub_key, _, sub_val = nxt.strip().partition(":")
                        child[sub_key.strip()] = sub_val.strip()
                        i += 1
                    elif not nxt.strip():
                        i += 1
                    else:
                        break
                if items:
                    result[key] = items
                elif child:
                    result[key] = child
                else:
                    result[key] = ""
                continue
            else:
                # 简单标量 · 去引号
                result[key] = value.strip('"\'')
                i += 1
                continue
        i += 1
    return result


def load_persona(investor_id: str) -> Persona | None:
    """根据 investor_id（如 'buffett' / 'zhao_lg'）读 YAML · 返 Persona 或 None."""
    path = PERSONAS_DIR / f"{investor_id}.yaml"
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        d = _parse_minimal_yaml(text)
        is_stub = False
        meta = d.get("_meta") or {}
        if isinstance(meta, dict):
            is_stub = meta.get("status") == "auto_generated_stub"
        return Persona(
            id=d.get("id", investor_id),
            name=d.get("name", ""),
            school=d.get("school", ""),
            group=d.get("group", ""),
            philosophy=d.get("philosophy", "") if isinstance(d.get("philosophy"), str) else "",
            key_metrics=d.get("key_metrics", []) if isinstance(d.get("key_metrics"), list) else [],
            avoids=d.get("avoids", []) if isinstance(d.get("avoids"), list) else [],
            a_share_view=d.get("a_share_view", "") if isinstance(d.get("a_share_view"), str) else "",
            voice=d.get("voice", "") if isinstance(d.get("voice"), str) else "",
            famous_positions=d.get("famous_positions", []) if isinstance(d.get("famous_positions"), list) else [],
            is_flagship=not is_stub,
            raw=d,
        )
    except Exception:
        return None


def load_all_personas() -> dict[str, Persona]:
    """加载全部 51 persona · 返 {id: Persona}."""
    result = {}
    for path in PERSONAS_DIR.glob("*.yaml"):
        p = load_persona(path.stem)
        if p and p.id:
            result[p.id] = p
    return result


FRAMEWORK_INSTRUCTIONS = """You are part of a multi-investor role-play analysis workbench.

Each turn you play one specific investor and judge a stock through their
philosophy + key_metrics + avoids + voice. Rules:

1. **Stay fully in character** — do not pretend to be neutral or hedge.
   - A value investor who hates richly-valued tech stocks should say so.
   - A macro investor judges the macro setup, not line-by-line fundamentals.
   - A technical/momentum trader reads price and volume, not DCF.

2. **Cite concrete data** — pull specific numbers from the SNAPSHOT: P/E, ROE,
   revenue, market cap, industry, etc.
   - BAD: "valuation is reasonable" → GOOD: "a P/E of 21 on a 30% ROE business is not expensive"
   - BAD: "fundamentals look fine" → GOOD: "revenue +27% but EPS flat — growth isn't converting to profit"

3. **Reference the persona's key_metrics** — state which screens pass and which fail.
   - Buffett: ROE > 15% for 10 straight years must be addressed.
   - Lynch: PEG < 1 must be computed.
   - Klarman: margin of safety vs. intrinsic value must be checked.

4. **Output a signal** — exactly one of bullish / neutral / bearish / skip (not a fit).
5. **Output a verdict** — e.g. Strong Buy / Buy / Watch / Hold / Avoid / Not a fit.
6. **Output reasoning** — 2-3 short paragraphs, in voice, citing data + key_metrics.

If the persona is an auto_generated_stub (_meta.status), lean on the concrete
rules the engine matched; the YAML voice only adds tone. Do not pretend to know
more than the rules do.

OUTPUT must be strict JSON:
{
  "investor_id": string,
  "signal": "bullish" | "neutral" | "bearish" | "skip",
  "score": 0-100,
  "verdict": string,
  "headline": string (< 80 chars · strong conclusion),
  "reasoning": string (2-3 paragraphs · in voice · cite data + key_metrics),
  "persona_used": "flagship" | "stub"
}"""

# Backwards-compat alias
FRAMEWORK_INSTRUCTIONS_ZH = FRAMEWORK_INSTRUCTIONS


def build_system_message(
    snapshot_json: str,
    lang: str = "en",
    include_flagship_tips: bool = True,
) -> str:
    """Build a prefix-stable system message (prompt-cache friendly).

    Every persona call uses this same system message; only the user message
    differs (persona switch), so the Anthropic/OpenAI prompt cache hits the
    shared prefix and saves 50-90% input tokens.
    """
    from lib.i18n import language_instruction
    parts = [
        FRAMEWORK_INSTRUCTIONS,
        "",
        language_instruction(lang),
        "",
        "# MARKET SNAPSHOT (shared by all personas — do not re-extract)",
        snapshot_json,
    ]
    return "\n".join(parts)


def build_persona_user_message(persona: Persona, ticker: str, task: str = "analyze") -> str:
    """Build the persona-specific user message: persona block + task instruction."""
    return (
        persona.to_prompt_block()
        + f"\n\n---\n\n# TASK\n"
        + f"Now, as {persona.name} ({persona.id}), analyze the stock {ticker}, "
        + f"strictly following the philosophy / key_metrics / voice above. "
        + f"Output a PersonaVote in JSON (see the format constraint at the end of the system message)."
    )


if __name__ == "__main__":
    # smoke test
    import json as _json
    all_p = load_all_personas()
    print(f"加载 persona: {len(all_p)}")
    flagship = [p for p in all_p.values() if p.is_flagship]
    stub = [p for p in all_p.values() if not p.is_flagship]
    print(f"  flagship: {len(flagship)} · {sorted(p.id for p in flagship)}")
    print(f"  stub: {len(stub)}")

    b = all_p.get("buffett")
    if b:
        print(f"\nBuffett persona block:\n{b.to_prompt_block()[:500]}")
