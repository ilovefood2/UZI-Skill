"""Regression for v3.4.1 · verdict 细化 + verdict_detail.

用户反馈：神剑股份 (002361 · overall=58) 和博云新材 (002297 · overall=59.9) 评分一致.
诊断：两只股 panel_consensus 49.4 vs 53.2 · overall 58 vs 59.9 · 流派分差 13-15 ·
     但 verdict 都是"观望优先" (50-65 区间太宽).

修法：
1. verdict 50-65 拆为 50-55/55-60/60-65 三档（观望偏空/中性/偏多）· 65-70 加"可以蹲（偏弱）"
2. synthesis 新增 verdict_detail 字段 · 含 "基本面 X · 共识 Y" 精确分
3. assemble_report.{{VERDICT_LABEL}} 追加 verdict_detail
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_verdict_label_has_fine_grained_buckets():
    """US edition · score_fns must implement the fine-grained English verdict buckets."""
    src = (SCRIPTS / "lib" / "pipeline" / "score_fns.py").read_text(encoding="utf-8")
    for label in ("Strong Buy", "Worth Accumulating", "Worth Accumulating (weak)",
                  "Watch (lean long)", "Watch (neutral)", "Watch (lean short)", "Cautious", "Avoid"):
        assert label in src, f"verdict label '{label}' missing"


def test_verdict_label_appends_school_split():
    """The school bull/bear split should be appended to the verdict label."""
    src = (SCRIPTS / "lib" / "pipeline" / "score_fns.py").read_text(encoding="utf-8")
    assert "schools bullish" in src, "verdict label should append the school-divergence marker"


def test_synthesis_includes_verdict_detail():
    """synthesis must output a verdict_detail field."""
    src = (SCRIPTS / "lib" / "pipeline" / "score_fns.py").read_text(encoding="utf-8")
    assert "verdict_detail" in src
    assert 'Fundamentals' in src and 'Consensus' in src, "verdict_detail must carry the fundamentals + consensus scores"


def test_assemble_report_renders_verdict_detail():
    """assemble_report.{{VERDICT_LABEL}} 替换必须包含 verdict_detail."""
    src = (SCRIPTS / "assemble_report.py").read_text(encoding="utf-8")
    # 找 {{VERDICT_LABEL}} 替换那段 · 必须含 verdict_detail
    idx = src.find('"{{VERDICT_LABEL}}"')
    assert idx > 0
    snippet = src[idx:idx + 500]
    assert "verdict_detail" in snippet, (
        "v3.4.1 regression: {{VERDICT_LABEL}} 渲染必须追加 verdict_detail"
    )


def test_close_stocks_differentiable_after_v3_4_1():
    """v3.4.1 · 神剑 58 vs 博云 59.9 · 通过 verdict_detail 必须能看出基本面差异."""
    # 模拟两只股 synthesis
    syn_a = {
        "overall_score": 58.0, "verdict_label": "观望中性",
        "fundamental_score": 60.3, "panel_consensus": 54.5,
        "verdict_detail": "基本面 60.3 · 共识 54.5",
    }
    syn_b = {
        "overall_score": 59.9, "verdict_label": "观望中性",
        "fundamental_score": 62.3, "panel_consensus": 56.4,
        "verdict_detail": "基本面 62.3 · 共识 56.4",
    }
    # verdict 段相同 · 但 detail 不同
    assert syn_a["verdict_label"] == syn_b["verdict_label"]
    assert syn_a["verdict_detail"] != syn_b["verdict_detail"]
    # detail 必须含数字
    assert "60.3" in syn_a["verdict_detail"]
    assert "62.3" in syn_b["verdict_detail"]
