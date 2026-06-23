"""Regression for v3.5.0 · 单一流派视角锁定.

用户需求：CLI 加 --school A/B/C/D/E/F/G 锁定单一流派评委 · 其他派自动 skip ·
报告顶部渲染 SCHOOL LOCK banner · agent role-play 也只覆盖该派.

测试覆盖：
1. evaluator.get_locked_school 正确解析 UZI_SCHOOL env
2. evaluator.evaluate 对非锁定派评委返 skip
3. evaluator.evaluate 对锁定派评委正常评分
4. _render_school_lock_banner 渲染 7 派各自配色
5. 未锁定时 banner 不渲染（不污染默认报告）
6. 流派标签映射完整 (7 派)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


# ─── #1 · get_locked_school 解析 env ─────────────────────

def test_locked_school_unset_returns_empty():
    from lib.investor_evaluator import get_locked_school
    os.environ.pop("UZI_SCHOOL", None)
    assert get_locked_school() == ""


def test_locked_school_lowercase_normalized():
    from lib.investor_evaluator import get_locked_school
    os.environ["UZI_SCHOOL"] = "g"
    try:
        assert get_locked_school() == "G"
    finally:
        os.environ.pop("UZI_SCHOOL", None)


def test_locked_school_invalid_ignored():
    """乱填的字母 · 不在 A-G 范围 · 当作未锁定."""
    from lib.investor_evaluator import get_locked_school
    os.environ["UZI_SCHOOL"] = "Z"
    try:
        assert get_locked_school() == ""
    finally:
        os.environ.pop("UZI_SCHOOL", None)


def test_school_labels_cover_seven_groups():
    from lib.investor_evaluator import SCHOOL_LABELS
    # US edition: schools A/B/C/D/G/H/I (China-value E and youzi F removed)
    assert set(SCHOOL_LABELS.keys()) == {"A", "B", "C", "D", "G", "H", "I"}
    for k, v in SCHOOL_LABELS.items():
        assert v and isinstance(v, str), f"{k} label missing"


# ─── #2 · evaluator skip 非锁定派 ────────────────────────

def test_evaluate_skips_non_locked_school():
    """Lock school D · buffett (school A) should skip · not enter the rule engine."""
    from lib.investor_evaluator import evaluate
    os.environ["UZI_SCHOOL"] = "D"
    try:
        features = {"market": "U", "ticker": "AAPL", "name": "Apple",
                    "industry": "Consumer Electronics", "market_cap_yi": 30000}
        result = evaluate("buffett", features)
        assert result["signal"] == "skip", "a school-A juror should skip under a D lock"
        assert "D" in result.get("skip_reason", "")
    finally:
        os.environ.pop("UZI_SCHOOL", None)


def test_evaluate_no_lock_does_not_skip():
    """未锁定 · 评委照常评分 (不被 v3.5.0 误伤)."""
    from lib.investor_evaluator import evaluate
    os.environ.pop("UZI_SCHOOL", None)
    features = {"market": "A", "ticker": "300394.SZ", "name": "天孚通信",
                "industry": "光器件", "market_cap_yi": 1500, "roe": 42, "pe_ttm": 154}
    result = evaluate("buffett", features)
    # 不应因 school_lock 而 skip · 可能因其他原因 skip 但理由不能是"锁定"
    if result["signal"] == "skip":
        assert "锁定" not in result.get("skip_reason", "")


# ─── #3 · banner 渲染 ──────────────────────────────────────

def test_school_lock_banner_renders_when_locked():
    from lib.report.institutional import _render_school_lock_banner
    syn = {"school_lock": {"group": "F", "label": "A 股游资"}}
    html = _render_school_lock_banner(syn)
    assert "SCHOOL LOCK" in html
    assert "F · A 股游资" in html
    assert "赵老哥" in html  # F 派代表评委提示


def test_school_lock_banner_empty_when_no_lock():
    from lib.report.institutional import _render_school_lock_banner
    assert _render_school_lock_banner({}) == ""
    assert _render_school_lock_banner({"school_lock": None}) == ""
    assert _render_school_lock_banner(None) == ""


def test_school_lock_banner_each_school_has_theme():
    """7 派各自的 banner 必须有配色 + 代表评委提示 · 不能用默认灰."""
    from lib.report.institutional import _render_school_lock_banner
    for g, label in [("A", "价值派"), ("B", "成长派"), ("C", "宏观派"),
                     ("D", "技术派"), ("E", "中国价投"), ("F", "A 股游资"), ("G", "量化")]:
        html = _render_school_lock_banner({"school_lock": {"group": g, "label": label}})
        assert "SCHOOL LOCK" in html
        assert g in html and label in html
        assert "rgba(107,114,128" not in html, f"{g} 派用了默认灰 · 应单独配色"


def test_school_lock_banner_unknown_group_falls_back():
    """非 A-G 的 group · 应优雅降级 · 不崩."""
    from lib.report.institutional import _render_school_lock_banner
    html = _render_school_lock_banner({"school_lock": {"group": "X", "label": "实验派"}})
    assert "SCHOOL LOCK" in html
    assert "X" in html or "实验派" in html


# ─── #4 · run.py argparse ────────────────────────────────

def test_run_py_has_school_argument():
    """US edition · run.py argparse must include --school with the kept schools."""
    run_py = (Path(__file__).resolve().parents[4] / "run.py").read_text(encoding="utf-8")
    assert '"--school"' in run_py
    # US edition: China-value E and youzi F removed
    assert 'choices=["A", "B", "C", "D", "G", "H", "I"]' in run_py
    # must set UZI_SCHOOL env for the evaluator to read
    assert 'UZI_SCHOOL' in run_py
