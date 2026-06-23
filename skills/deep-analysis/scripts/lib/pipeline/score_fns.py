"""pipeline.score_fns · 纯函数 · 从 run_real_test.py 搬迁 (v3.1).

### 搬迁内容
- `_f(v, default)` · 安全 float 解析（百分号 / 逗号 / 中文货币）
- `score_dimensions(raw)` · 22 维打分
- `generate_panel(dims_scored, raw)` · 51 评委投票 + school_scores
- `_auto_summarize_dim(dim_key, label, dim, score)` · 维度摘要
- `_autofill_qualitative_via_mx(raw, ticker)` · MX 兜底（原地改 raw）
- `_extract_mx_text(result)` · MX 响应解析 helper
- `generate_synthesis(raw, dims_scored, panel, agent_analysis=None)` · 综合研判

### 为什么独立模块
v2.15.x 连续 hotfix 集中在 run_real_test.py (2105 行) · 业务函数和 CLI 入口混杂。
v3.1 拆分：纯函数放这里 · rrt.py 只剩 stage1/stage2/main CLI 入口 + collect_raw_data.

### 向后兼容
rrt.py 仍 re-export 这些函数 (from lib.pipeline.score_fns import *)· 所有
`rrt.score_dimensions(...)` / `rrt.generate_panel(...)` / `rrt.generate_synthesis(...)`
调用保持工作 · pipeline.score 和 legacy 都能调.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

# rrt 当前 sys.path 里的依赖（由 rrt 加入 · score_fns 只要 import）
from lib.investor_db import INVESTORS
from lib.investor_personas import get_comment as _persona_comment
from lib.investor_evaluator import evaluate as _evaluate_investor
from lib.stock_features import extract_features
from lib.market_router import parse_ticker


# ═══════════════════════════════════════════════════════════════
# 以下为从 run_real_test.py 原样搬迁的纯函数（保持行为零差异）
# 搬迁日期：v3.1 · 2026-04-23
# ═══════════════════════════════════════════════════════════════


def _f(v, default=0.0):
    try:
        return float(str(v).replace("%", "").replace(",", "").replace("+", ""))
    except (ValueError, TypeError):
        return default


def score_dimensions(raw: dict) -> dict:
    dims = raw.get("dimensions", {})
    out = {}

    def _get(key: str) -> dict:
        return (dims.get(key) or {}).get("data") or {}

    # 1 · 财报
    fin = _get("1_financials")
    roe = _f(fin.get("roe"))
    last_roe = (fin.get("roe_history") or [0])[-1] if fin.get("roe_history") else roe
    net_margin = _f(fin.get("net_margin"))
    health = fin.get("financial_health") or {}
    debt = _f(health.get("debt_ratio"))
    rev_hist = fin.get("revenue_history") or []
    growth = ((rev_hist[-1] - rev_hist[-2]) / rev_hist[-2] * 100) if len(rev_hist) >= 2 and rev_hist[-2] else 0
    score_1 = 5
    if last_roe >= 15: score_1 += 2
    elif last_roe >= 10: score_1 += 1
    elif last_roe < 5: score_1 -= 2
    if net_margin >= 15: score_1 += 1
    if growth >= 20: score_1 += 1
    if debt >= 60: score_1 -= 1
    score_1 = max(1, min(10, score_1))
    reasons_pass_1 = []
    reasons_fail_1 = []
    if last_roe >= 15: reasons_pass_1.append(f"ROE latest {last_roe:.1f}%")
    elif last_roe < 8: reasons_fail_1.append(f"ROE latest {last_roe:.1f}% is low")
    if growth >= 20: reasons_pass_1.append(f"revenue growth {growth:.1f}%")
    elif growth < 5: reasons_fail_1.append(f"revenue growth {growth:.1f}% stalled")
    if debt < 40: reasons_pass_1.append(f"debt ratio {debt:.0f}% healthy")
    elif debt > 60: reasons_fail_1.append(f"debt ratio {debt:.0f}% elevated")
    out["1_financials"] = {"score": score_1, "weight": 5,
                            "label": f"ROE {last_roe:.1f}% · rev growth {growth:+.1f}% · debt {debt:.0f}%",
                            "reasons_pass": reasons_pass_1, "reasons_fail": reasons_fail_1}

    # 2 · K 线
    kline = _get("2_kline")
    stage = str(kline.get("stage", ""))
    ma_align = str(kline.get("ma_align", ""))
    stats = kline.get("kline_stats") or {}
    score_2 = 5
    if "Stage 2" in stage: score_2 += 2
    elif "Stage 1" in stage: score_2 += 1
    elif "Stage 3" in stage or "Stage 4" in stage: score_2 -= 2
    if "多头" in ma_align: score_2 += 1
    dd_str = stats.get("max_drawdown", "0%")
    dd = _f(dd_str)
    if dd <= -30: score_2 -= 1
    score_2 = max(1, min(10, score_2))
    label_2 = f"{stage} · MA {ma_align}"
    if stats.get("ytd_return"): label_2 += f" · YTD {stats['ytd_return']}"
    out["2_kline"] = {"score": score_2, "weight": 4, "label": label_2,
                      "reasons_pass": [f"{stage}"] if "Stage 2" in stage else [],
                      "reasons_fail": [f"max drawdown {dd:.1f}%"] if dd <= -25 else []}

    # 3 · macro (qualitative — give middle)
    out["3_macro"] = {"score": 6, "weight": 3, "label": "Macro backdrop neutral"}

    # 4 · 同行
    peers = _get("4_peers")
    peer_table = peers.get("peer_table") or []
    score_4 = 5
    if peer_table and len(peer_table) > 1:
        score_4 = 7  # we have data
        try:
            self_row = next((p for p in peer_table if p.get("is_self")), None)
            if self_row:
                self_pe = _f(self_row.get("pe"))
                avg_pe = sum(_f(p.get("pe")) for p in peer_table if not p.get("is_self")) / max(1, len([p for p in peer_table if not p.get("is_self")]))
                if self_pe > 0 and avg_pe > 0:
                    if self_pe < avg_pe * 0.9: score_4 += 1
                    elif self_pe > avg_pe * 1.2: score_4 -= 1
        except Exception:
            pass
    out["4_peers"] = {"score": score_4, "weight": 4,
                      "label": f"{len(peer_table) - 1} peers compared" if peer_table else "no peer data",
                      "reasons_pass": [], "reasons_fail": []}

    # 5 · supply chain
    chain = _get("5_chain")
    breakdown = chain.get("main_business_breakdown") or []
    score_5 = 6 if breakdown else 5
    out["5_chain"] = {"score": score_5, "weight": 4,
                      "label": f"{len(breakdown)} business segments identified" if breakdown else "supply-chain data incomplete",
                      "reasons_pass": [], "reasons_fail": []}

    # 6 · 研报
    research = _get("6_research")
    coverage = research.get("report_count", 0)
    ratings = research.get("rating_distribution") or {}
    buy_count = sum(v for k, v in ratings.items() if "buy" in str(k).lower() or "overweight" in str(k).lower() or "买入" in str(k) or "增持" in str(k))
    score_6 = 5 + min(3, coverage // 5)
    if buy_count >= 10: score_6 += 1
    score_6 = min(10, score_6)
    out["6_research"] = {"score": score_6, "weight": 3,
                         "label": f"{coverage} analyst reports · {buy_count} Buy/Overweight" if coverage else "sparse analyst coverage",
                         "reasons_pass": [f"{coverage} firms covering"] if coverage >= 10 else [],
                         "reasons_fail": [] if coverage else ["lacks coverage"]}

    # 7 · industry (stub heavy qualitative)
    out["7_industry"] = {"score": 7, "weight": 4, "label": "Industry in a growth phase"}

    # 8 · raw materials
    out["8_materials"] = {"score": 6, "weight": 3, "label": "Input-cost watch"}

    # 10 · 估值
    val = _get("10_valuation")
    pe_q_str = str(val.get("pe_quantile", ""))
    import re
    m = re.search(r'(\d+)', pe_q_str)
    pe_q = int(m.group(1)) if m else 50
    score_10 = 5
    if pe_q < 30: score_10 = 9
    elif pe_q < 50: score_10 = 7
    elif pe_q < 70: score_10 = 5
    elif pe_q < 85: score_10 = 3
    else: score_10 = 2
    out["10_valuation"] = {"score": score_10, "weight": 5,
                            "label": f"P/E {val.get('pe', '—')} · {pe_q}th 5-yr percentile · industry avg {val.get('industry_pe', '—')}",
                            "reasons_pass": ["P/E below its 5-yr median"] if pe_q < 50 else [],
                            "reasons_fail": ["P/E in its 5-yr high zone"] if pe_q >= 75 else []}

    # 11 · 治理
    gov = _get("11_governance")
    pledge = gov.get("pledge") or []
    has_insider = bool(gov.get("insider_trades_1y"))
    score_11 = 6
    if not pledge or (isinstance(pledge, list) and len(pledge) == 0): score_11 += 1
    if has_insider: score_11 += 1
    out["11_governance"] = {"score": min(10, score_11), "weight": 4,
                             "label": f"pledge records {len(pledge) if isinstance(pledge, list) else '—'} · insider trades {'yes' if has_insider else 'no'}"}

    # 14 · moat
    out["14_moat"] = {"score": 6, "weight": 3, "label": "Moat needs qualitative review"}

    # 15 · events
    events = _get("15_events")
    news = events.get("news") or []
    notices = events.get("recent_notices") or []
    score_15 = 5 + min(3, len(news) // 10)
    out["15_events"] = {"score": score_15, "weight": 4,
                        "label": f"{len(news)} recent news · {len(notices)} filings"}

    # 17 · 舆情 / sentiment
    hot = _get("17_sentiment")
    hot_rank = (hot.get("hot_rank") or {}).get("rank_history") or []
    score_17 = 6 + min(2, len(hot_rank) // 10)
    out["17_sentiment"] = {"score": score_17, "weight": 3,
                            "label": f"social-sentiment mentions {len(hot_rank)}"}

    # Overall fundamental score
    total_weighted = sum(v["score"] * v["weight"] for v in out.values())
    total_weight = sum(v["weight"] for v in out.values())
    fundamental = (total_weighted / total_weight * 10) if total_weight else 0

    return {"ticker": raw["ticker"], "fundamental_score": round(fundamental, 1), "dimensions": out}


# ─────────── PANEL GENERATION (rule-based) ───────────

def generate_panel(dims_scored: dict, raw: dict) -> dict:
    """Rule-engine-based panel — each investor's verdict cites specific
    criteria from investor_criteria.py that were hit or missed.
    """
    # Build the flat feature dict once for all 51 investors
    features = extract_features(raw, raw.get("dimensions", {}))

    basic_ctx = (raw.get("dimensions", {}).get("0_basic") or {}).get("data") or {}
    kline_ctx = (raw.get("dimensions", {}).get("2_kline") or {}).get("data") or {}
    fin_ctx = (raw.get("dimensions", {}).get("1_financials") or {}).get("data") or {}

    investors_out = []
    vote_dist = {"strongly_buy": 0, "buy": 0, "watch": 0, "wait": 0, "avoid": 0, "n_a": 0, "skip": 0}
    sig_dist = {"bullish": 0, "neutral": 0, "bearish": 0, "skip": 0}

    def _score_to_verdict(score: float, signal: str) -> str:
        if signal == "bullish" and score >= 80:
            return "Strong Buy"
        if signal == "bullish":
            return "Buy"
        if signal == "bearish" and score <= 20:
            return "Avoid"
        if signal == "bearish":
            return "Hold"
        # neutral
        return "Watch" if score >= 50 else "Hold"

    for inv in INVESTORS:
        inv_id = inv["id"]
        verdict_obj = _evaluate_investor(inv_id, features)

        sig = verdict_obj["signal"]
        score = int(max(0, verdict_obj["score"]))
        confidence = int(verdict_obj["confidence"])

        # Handle "skip" — investor won't look at this market
        if sig == "skip":
            verdict = "Not a fit"
            score = 0
            confidence = 0
            skip_reason = verdict_obj.get("skip_reason", "outside circle of competence")
            headline = f"Not a fit — {skip_reason}"
            comment = f"Outside my circle of competence — no opinion.\n{headline}"
            reasoning = verdict_obj.get("rationale", "")
        else:
            verdict = _score_to_verdict(score, sig)

            # Persona voice layer
            ctx = {
                "name": basic_ctx.get("name", "这只票"),
                "industry": basic_ctx.get("industry", "该行业"),
                "price": basic_ctx.get("price", "—"),
                "pe": basic_ctx.get("pe_ttm", "—"),
                "roe": str((fin_ctx.get("roe_history") or ["—"])[-1]),
                "stage": kline_ctx.get("stage", "—"),
                "growth": fin_ctx.get("revenue_growth", "—"),
            }
            persona_line = _persona_comment(inv_id, sig, ctx)

            headline = verdict_obj["headline"]
            comment = f"{persona_line}\n{headline}"
            reasoning = verdict_obj["rationale"]

        v_key = {"Strong Buy": "strongly_buy", "Buy": "buy", "Watch": "watch",
                 "Hold": "wait", "Avoid": "avoid", "Not a fit": "skip"}.get(verdict, "n_a")
        vote_dist[v_key] = vote_dist.get(v_key, 0) + 1
        sig_dist[sig] = sig_dist.get(sig, 0) + 1

        investors_out.append({
            "investor_id": inv_id,
            "name": inv["name"],
            "group": inv["group"],
            "avatar": f"avatars/{inv_id}.svg",
            "signal": sig,
            "confidence": confidence,
            "score": score,
            "verdict": verdict,
            "reasoning": reasoning,
            "comment": comment,
            "headline": headline,
            "pass": [{"name": r["name"], "msg": r["msg"], "weight": r["weight"]}
                     for r in verdict_obj["pass_rules"][:4]],
            "fail": [{"name": r["name"], "msg": r["msg"], "weight": r["weight"]}
                     for r in verdict_obj["fail_rules"][:4]],
            "weight_pass": verdict_obj["weight_pass"],
            "weight_total": verdict_obj["weight_total"],
            "ideal_price": None,
            "period": "中长线" if inv["group"] in ("A", "B", "E") else "短线",
            # v2.8 · 因地制宜：每个评委用自己方法论回答这 3 个问题
            "time_horizon": verdict_obj.get("time_horizon", "—"),
            "position_sizing": verdict_obj.get("position_sizing", "—"),
            "what_would_change_my_mind": verdict_obj.get("what_would_change_my_mind", "—"),
        })

    # v2.15.5 · 混合 consensus 公式（连续分 + 离散票）
    # 动机：v2.11 单一公式 `(bullish + 0.6*neutral)/active*100` 只看 signal 计数 ·
    # 把连续 score 压成 3 分类 · 导致 331 个打分中 bullish:neutral:bearish=9.9:13:18.5 ·
    # 多数股 consensus 聚集 40-55 区间分不开.
    # 实测：单 investor score stdev=30.3 信息很丰富 · 但 consensus stdev 只有 28.2 还聚集 ·
    # 说明 signal 分类丢失了"程度"信息（55 和 40 都算 neutral 但态度不同）.
    #
    # 新公式：consensus = 0.65 * score_mean + 0.35 * vote_weighted
    #   - score_mean:  active 成员 score 均值（连续 0-100 · 反映强度）
    #   - vote_weighted: 原 (bullish + 0.6*neutral)/active*100（保留投票机制）
    # 学派级 school_scores 同样用混合公式 · 让各流派分数拉开.
    # 回归风险：v2.11 下 65 分 = "可以蹲一蹲" · 新公式下因 score_mean 参与，
    # 历史白马可能从 40+ 涨到 55+ · 属校准而非 bug · overall 阈值不变.
    NEUTRAL_WEIGHT = 0.6
    SCORE_WEIGHT = 0.65   # score 均值权重（连续分 · 区分度）
    VOTE_WEIGHT  = 0.35   # vote 比例权重（离散投票 · 稳定性）
    POLARIZE_K = 1.30     # 极化系数 · >1 让两端拉开 · 50 为中心
    active_count = len(investors_out) - sig_dist.get("skip", 0)
    bullish = sig_dist.get("bullish", 0)
    neutral = sig_dist.get("neutral", 0)

    def _polarize(c: float, k: float = POLARIZE_K) -> float:
        """极化拉伸 · 50 为中心 · 距离 * k · 裁剪到 [0, 100].

        目的：rule-engine 评分先天居中（大多股 35-65 区间）· 聚合后 consensus
        更居中 · 用户反馈"大多数分在一个区间徘徊"· 极化让强势 70→86 · 弱势 22→14.
        保留 50 为"及格线"不动 · 只放大距离.
        """
        return max(0.0, min(100.0, 50.0 + (c - 50.0) * k))

    # 分量 1 · score 均值（active only · skip 不计）
    active_scores = [m["score"] for m in investors_out if m.get("signal") != "skip"]
    score_mean = (sum(active_scores) / len(active_scores)) if active_scores else 50.0
    # 分量 2 · vote 比例（原 v2.11 公式）
    vote_weighted = (bullish + NEUTRAL_WEIGHT * neutral) / max(active_count, 1) * 100
    consensus_raw = SCORE_WEIGHT * score_mean + VOTE_WEIGHT * vote_weighted
    consensus = _polarize(consensus_raw)

    # v2.15.4+ · 按流派打分（v2.15.5 同步升级为混合公式）
    # 譬如白马消费股：价值派 85 分（重仓），技术派 30 分（趋势破位）·
    # 现在可以一眼看出"不同哲学得出的结论有多不同"
    GROUP_META = {
        "A": {"label": "Classic Value", "desc": "Buffett / Graham / Fisher / Munger lineage"},
        "B": {"label": "Growth",        "desc": "Lynch / O'Neil / Thiel / Wood lineage"},
        "C": {"label": "Macro",         "desc": "Soros / Dalio / Marks lineage"},
        "D": {"label": "Technical",     "desc": "Livermore / Minervini / Darvas lineage"},
        "G": {"label": "Quant",         "desc": "Simons / Thorp / Shaw lineage"},
        "H": {"label": "Tech Leaders",  "desc": "Jensen Huang / Musk / Altman / Saylor lineage"},
        "I": {"label": "AI Bottleneck Hunter", "desc": "Serenity · AI supply-chain chokepoints"},
    }

    def _consensus_to_verdict(c: float) -> str:
        """School-level verdict · thresholds match the composite score (80/65/50/35)."""
        if c >= 80: return "Overweight"
        if c >= 65: return "Buy"
        if c >= 50: return "Watch"
        if c >= 35: return "Cautious"
        return "Avoid"

    by_group: dict[str, list[dict]] = {}
    for inv in investors_out:
        by_group.setdefault(inv.get("group", "?"), []).append(inv)

    school_scores: dict[str, dict] = {}
    for g in sorted(by_group.keys()):
        members = by_group[g]
        n_members = len(members)
        active_m = [m for m in members if m.get("signal") != "skip"]
        n_active = len(active_m)
        g_bull = sum(1 for m in members if m.get("signal") == "bullish")
        g_neu  = sum(1 for m in members if m.get("signal") == "neutral")
        g_bear = sum(1 for m in members if m.get("signal") == "bearish")
        g_skip = sum(1 for m in members if m.get("signal") == "skip")

        # v2.15.5 · 流派级混合公式（与总盘保持一致 · 同样极化）
        if n_active > 0:
            s_score_mean = sum(m.get("score", 0) for m in active_m) / n_active
            s_vote = (g_bull + NEUTRAL_WEIGHT * g_neu) / n_active * 100
            s_raw = SCORE_WEIGHT * s_score_mean + VOTE_WEIGHT * s_vote
            s_consensus = _polarize(s_raw)
        else:
            s_score_mean = 0.0
            s_vote = 0.0
            s_consensus = 0.0

        # 主流信号
        sig_counts = [("bullish", g_bull), ("neutral", g_neu), ("bearish", g_bear)]
        dominant = max(sig_counts, key=lambda x: x[1])[0] if n_active > 0 else "skip"

        meta = GROUP_META.get(g, {"label": g, "desc": ""})
        school_scores[g] = {
            "group": g,
            "label": meta["label"],
            "desc": meta["desc"],
            "n_members": n_members,
            "n_active": n_active,
            "consensus": round(s_consensus, 1),
            "avg_score": round(s_score_mean, 1),  # alias · 兼容 v2.15.4 字段
            "vote_consensus": round(s_vote, 1),   # v2.15.5 · vote 分量（可视化展开用）
            "score_mean": round(s_score_mean, 1), # v2.15.5 · score 分量 · 明确语义
            "verdict": _consensus_to_verdict(s_consensus) if n_active > 0 else "Not a fit",
            "bullish": g_bull,
            "neutral": g_neu,
            "bearish": g_bear,
            "skip": g_skip,
            "dominant_signal": dominant,
        }

    return {
        "ticker": raw["ticker"],
        "panel_consensus": round(consensus, 1),
        "vote_distribution": vote_dist,
        "signal_distribution": sig_dist,
        "investors": investors_out,
        # v2.15.4 · 按流派分数 · 7 个 school 各自 consensus/avg_score/verdict
        "school_scores": school_scores,
        # v2.15.5 · 诊断字段 · 混合公式各分量 + 极化前后值
        "consensus_formula": {
            "version": "v2.15.5 · polarize(0.65*score_mean + 0.35*vote_weighted, k=1.3)",
            "score_weight": SCORE_WEIGHT,
            "vote_weight": VOTE_WEIGHT,
            "neutral_weight": NEUTRAL_WEIGHT,
            "polarize_k": POLARIZE_K,
            "score_mean": round(score_mean, 2),
            "vote_weighted": round(vote_weighted, 2),
            "consensus_raw": round(consensus_raw, 2),     # 极化前
            "consensus_final": round(consensus, 2),        # 极化后（= panel_consensus）
            "bullish": bullish,
            "neutral_weighted": round(neutral * NEUTRAL_WEIGHT, 2),
            "bearish": sig_dist.get("bearish", 0),
            "skip": sig_dist.get("skip", 0),
            "active": active_count,
        },
    }


# ─────────────────────────────────────────────────────────────
# v2.6.1 · 自动综合各维度 raw_data 字段为可读 commentary
# 替代旧版 "[脚本占位]" 废话；让直跑模式（无 agent）也能产出有信息量的报告
# Agent 介入时仍可覆盖（agent_analysis.dim_commentary 优先级最高）
# ─────────────────────────────────────────────────────────────
def _auto_summarize_dim(dim_key: str, label: str, dim: dict, score: float) -> str:
    """Build a one-paragraph commentary from raw_data fields. NEVER returns
    placeholder strings — either real content or empty."""
    if not isinstance(dim, dict):
        return ""
    data = dim.get("data") or {}
    if not data:
        return f"{label}: no data fetched (fetcher failed or returned empty)."

    def _v(*keys, default="—"):
        for k in keys:
            v = data.get(k)
            if v not in (None, "", "—", "-", [], {}):
                return v
        return default

    def _join_list(lst, max_n=3, sep="; "):
        if not isinstance(lst, list) or not lst:
            return None
        out = []
        for x in lst[:max_n]:
            if isinstance(x, dict):
                t = x.get("title") or x.get("name") or x.get("date") or str(x)
                out.append(str(t)[:50])
            else:
                out.append(str(x)[:50])
        return sep.join(out)

    # ─── Per-dim auto summarizer ───
    if dim_key == "0_basic":
        return f"{label}: {_v('name')} ({_v('code')}), {_v('industry')} sector. Market cap {_v('market_cap')}, P/E {_v('pe_ttm')}, P/B {_v('pb')}."

    if dim_key == "1_financials":
        roe = _v("roe_latest", "roe")
        rev_g = _v("revenue_growth_yoy", "revenue_yoy")
        np_g = _v("net_profit_yoy")
        margin = _v("net_margin", "gross_margin")
        return f"{label}: ROE {roe}, revenue YoY {rev_g}, net profit YoY {np_g}, net margin {margin}. Score {score}/10."

    if dim_key == "2_kline":
        stage = _v("stage", "wyckoff_stage")
        ma = _v("ma_align", "trend")
        macd = _v("macd")
        return f"{label}: {stage} · MA {ma} · MACD {macd}."

    if dim_key == "3_macro":
        return (f"{label}: rate cycle {_v('rate_cycle')}; FX {_v('fx_trend')}; "
                f"geopolitics {_v('geo_risk')}; commodities {_v('commodity', 'commodity_trend')}. "
                f"Score {score}/10.")

    if dim_key == "4_peers":
        rank = _v("rank")
        peer_table = data.get("peer_table") or []
        ind = _v("industry")
        peers_str = _join_list([p.get("name") for p in peer_table if isinstance(p, dict) and not p.get("is_self")][:5], max_n=5, sep=", ")
        return f"{label}: {ind} sector, {rank}{(', key peers: ' + peers_str) if peers_str else ''}. Score {score}/10."

    if dim_key == "5_chain":
        return f"{label}: upstream {_v('upstream')}; downstream {_v('downstream')}; customer concentration {_v('client_concentration')}."

    if dim_key == "6_research":
        rep_count = _v("report_count", "n_reports")
        target = _v("avg_target_price", "target_price")
        rating = _v("consensus_rating", "rating")
        return f"{label}: {rep_count} recent analyst reports, consensus rating {rating}, average target price {target}."

    if dim_key == "7_industry":
        ind_pe = _v("industry_pe_weighted") or (data.get("cninfo_metrics") or {}).get("industry_pe_weighted")
        ind_count = _v("total_companies") or (data.get("cninfo_metrics") or {}).get("company_count")
        growth = _v("growth")
        return f"{label}: sector {_v('industry')} · weighted industry P/E {ind_pe} · listed companies {ind_count} · growth {growth}."

    if dim_key == "8_materials":
        core = _v("core_material")
        trend = _v("price_trend")
        cost = _v("cost_share")
        return f"{label}: core input {core}; recent price trend {trend}; share of cost {cost}."

    if dim_key == "10_valuation":
        pe_q = _v("pe_quantile_5y", "pe_quantile")
        pb_q = _v("pb_quantile_5y", "pb_quantile")
        return f"{label}: P/E 5-yr percentile {pe_q}, P/B 5-yr percentile {pb_q}. Score {score}/10."

    if dim_key == "11_governance":
        ctrl = _v("actual_controller")
        recent = _v("recent_changes", "recent_holdings_change")
        return f"{label}: controlling owner {ctrl}; recent changes {recent}."

    if dim_key == "14_moat":
        scores = data.get("scores") or {}
        total = sum(scores.values()) if scores else None
        if total is not None:
            return f"{label}: four-forces score — intangibles {scores.get('intangible')}/10, switching cost {scores.get('switching')}/10, network effects {scores.get('network')}/10, scale {scores.get('scale')}/10 · total {total}/40."
        return f"{label}: limited data, score {score}/10."

    if dim_key == "15_events":
        timeline = data.get("event_timeline") or []
        recent_news = data.get("recent_news") or []
        if timeline:
            head = "; ".join([str(t)[:60] for t in timeline[:3]])
            return f"{label}: {len(timeline)} recent events, incl.: {head}."
        if recent_news:
            head = "; ".join([(n.get("title") or "")[:60] for n in recent_news[:3]])
            return f"{label}: {len(recent_news)} recent news items, incl.: {head}."
        return f"{label}: no notable events (fetcher returned empty)."

    if dim_key == "17_sentiment":
        hot = _v("hot_rank", "hot_score")
        senti = _v("sentiment_label", "sentiment")
        return f"{label}: heat {hot}; sentiment {senti}."

    # Default: just enumerate top fields
    items = []
    for k, v in list(data.items())[:5]:
        if v not in (None, "", "—", "-", [], {}) and not str(k).startswith("_"):
            items.append(f"{k}={str(v)[:30]}")
    return f"{label}: {', '.join(items) if items else 'no data'}." if items else ""


# v2.12.1 · MX/ddgs 返回垃圾数据的黑名单
# v2.13.0 · 抽到 lib/junk_filter.py 共用（Playwright 兜底也用）· 此处保留 BC delegate
try:
    from lib.junk_filter import JUNK_PATTERNS as _AUTOFILL_JUNK_PATTERNS, is_junk_autofill_text as _is_junk_autofill
except ImportError:
    # 兜底：旧环境直接内联定义（防止模块导入失败时整个文件崩）
    _AUTOFILL_JUNK_PATTERNS = (
        "类型；类型", "XXX", "TODO", "null", "undefined", "None",
        "抱歉，", "无法回答", "我不知道", "不清楚", "暂无数据",
        "（示例）", "（待补）",
    )
    def _is_junk_autofill(text):
        if not text: return True
        t = str(text).strip()
        if len(t) < 5: return True
        if any(j in t for j in _AUTOFILL_JUNK_PATTERNS): return True
        parts = [p.strip() for p in t.split("；") if p.strip()]
        return len(parts) >= 2 and len(set(parts)) == 1


def _autofill_qualitative_via_mx(raw: dict, ticker: str) -> None:
    """v2.6.1 · 自动补齐 6 个定性维度的空字段（in-place 修改 raw['dimensions']）.

    优先级：MX 妙想 API → ddgs WebSearch → 显式标记 autofill_failed。
    适用场景：直跑模式（无 agent 介入），fetcher 拿到空数据时不能让报告也空。

    v2.12.1 加入 _is_junk_autofill 质量过滤 · 垃圾数据（"类型；类型" 等）不写入字段.
    """
    try:
        from lib.mx_api import MXClient
    except ImportError:
        MXClient = None
    try:
        from lib.web_search import search as _ws_search
    except ImportError:
        _ws_search = None

    client = MXClient() if MXClient else None
    mx_ok = client is not None and client.available
    if not mx_ok and not _ws_search:
        print("   ⚠️ MX_APIKEY 未设置且 ddgs 不可用，跳过自动兜底")
        return

    dims = raw.get("dimensions", {})
    basic = (dims.get("0_basic") or {}).get("data") or {}
    name = basic.get("name") or ticker
    industry = basic.get("industry") or "综合"
    code_raw = ticker.split(".")[0] if "." in ticker else ticker

    def _is_default_or_empty(v) -> bool:
        """True if value is missing OR a generic-default placeholder."""
        if v in (None, "", "—", "-", [], {}, "n/a", "N/A"):
            return True
        s = str(v)
        # 这些都是 fetcher 的默认 fallback 字符串，没真实信息量
        if any(kw in s for kw in ["中性（", "中性(", "未拉取", "未命中", "无直接关联"]):
            return True
        return False

    # 6 个定性维度的"空判定" + MX query 模板（v2.6.1 加严：默认值也算空）
    targets = [
        ("3_macro",     lambda d: all(_is_default_or_empty(d.get(k)) for k in ("rate_cycle","fx_trend","geo_risk","commodity")),
                        lambda: f"{industry} 2026 宏观环境 利率周期 汇率 大宗商品 行业影响"),
        ("7_industry",  lambda d: _is_default_or_empty(d.get("growth")) and not (d.get("cninfo_metrics") or {}).get("industry_pe_weighted"),
                        lambda: f"{industry} 2026 行业增速 TAM 市场规模 渗透率"),
        ("8_materials", lambda d: _is_default_or_empty(d.get("core_material")),
                        lambda: f"{name} {code_raw} 主营业务 主要原材料 成本构成"),
        ("9_futures",   lambda d: _is_default_or_empty(d.get("linked_contract")) or "无直接" in str(d.get("linked_contract","")),
                        lambda: f"{industry} 行业 上下游 期货品种 套保 大宗"),
        ("13_policy",   lambda d: not any((d.get("snippets") or {}).get(k) for k in ("policy_dir","subsidy","monitoring","anti_trust")),
                        lambda: f"{industry} 2026 国家政策 监管动态 补贴 税收 影响"),
        ("15_events",   lambda d: not d.get("event_timeline") and not d.get("recent_news") and not d.get("recent_notices"),
                        lambda: f"{name} {code_raw} 最新公告 重大事件 业绩 合同"),
    ]
    fixed_count = 0
    skipped_full = 0
    failed_count = 0
    for dim_key, is_empty_fn, query_fn in targets:
        dim = dims.get(dim_key) or {}
        data = dim.get("data") or {}
        try:
            if not is_empty_fn(data):
                skipped_full += 1
                continue  # 该维度已有真实数据
        except Exception:
            skipped_full += 1
            continue

        query = query_fn()
        text = ""
        source_used = None

        # 优先 MX
        if mx_ok:
            try:
                r = client.query(query)
                text = _extract_mx_text(r)
                # v2.12.1 · 过滤 MX 返回的垃圾数据（"类型；类型"/"抱歉"/重复等）
                if _is_junk_autofill(text):
                    text = ""
                if text:
                    source_used = "mx_api"
            except Exception:
                pass

        # 回退 ddgs WebSearch
        if not text and _ws_search:
            try:
                results = _ws_search(query, max_results=3) or []
                snippets = []
                for r in results[:3]:
                    if isinstance(r, dict):
                        title = (r.get("title") or "").strip()
                        body = (r.get("body") or "").strip()
                        if title or body:
                            snippets.append(f"{title} — {body[:80]}".strip(" —"))
                text = "；".join(snippets)[:300]
                # v2.12.1 · 过滤 ddgs 拼接后的噪音（长度过短 / 模板占位符）
                if _is_junk_autofill(text):
                    text = ""
                if text:
                    source_used = "ddgs"
            except Exception:
                pass

        if text:
            data.setdefault("_autofill", {})
            data["_autofill"]["query"] = query
            data["_autofill"]["snippet"] = text
            data["_autofill"]["source"] = source_used
            # 把内容塞到对应字段，方便 _auto_summarize_dim 摘要
            if dim_key == "3_macro":
                data["rate_cycle"] = (text[:80] + "…") if len(text) > 80 else text
            elif dim_key == "7_industry":
                data["growth"] = (text[:80] + "…") if len(text) > 80 else text
            elif dim_key == "8_materials":
                data["core_material"] = (text[:60] + "…") if len(text) > 60 else text
            elif dim_key == "9_futures":
                data["contract_trend"] = (text[:60] + "…") if len(text) > 60 else text
            elif dim_key == "13_policy":
                snippets = data.setdefault("snippets", {})
                snippets.setdefault("policy_dir", []).append({"title": text[:120], "url": "", "source": source_used})
            elif dim_key == "15_events":
                data["event_timeline"] = [text[:120]]
            dims[dim_key] = {"ticker": ticker, "data": data,
                             "source": (dim.get("source", "") + f"+autofill:{source_used}").lstrip("+"),
                             "fallback": True}
            fixed_count += 1
            print(f"   ✓ {dim_key:14s} via {source_used}: {text[:60]}{'…' if len(text)>60 else ''}")
        else:
            data["_autofill_failed"] = {"query": query, "reason": "MX/ddgs 都没有返回内容"}
            dims[dim_key] = {"ticker": ticker, "data": data,
                             "source": (dim.get("source", "") + "+autofill_failed").lstrip("+"),
                             "fallback": True}
            failed_count += 1
            print(f"   ⚠️ {dim_key:14s} 兜底失败 · agent 应主动 web search 补抓")

    print(f"   合计 · 充足 {skipped_full} · 兜底成功 {fixed_count} · 失败 {failed_count}（共 6 维）")


def _extract_mx_text(result: dict) -> str:
    """Pull most readable text from MX query response.
    First tries dataTableDTOList[].title + entityName; else returns empty."""
    if not isinstance(result, dict) or result.get("error"):
        return ""
    data = result.get("data") or {}
    inner = data.get("data") or {}
    sr = inner.get("searchDataResultDTO") or {}
    dto_list = sr.get("dataTableDTOList") or []
    if not dto_list:
        # Try inner.entityName as last resort
        return str(inner.get("entityName") or "")[:200]
    parts = []
    for dto in dto_list[:2]:
        if not isinstance(dto, dict):
            continue
        title = dto.get("title") or dto.get("entityName") or ""
        if title:
            parts.append(str(title)[:120])
    return "；".join(parts)[:300] if parts else ""


def generate_synthesis(raw: dict, dims_scored: dict, panel: dict, agent_analysis: dict | None = None) -> dict:
    """Generate synthesis — merges agent_analysis.json if provided.

    agent_analysis keys (all optional, agent writes what it has):
      - dim_commentary: {dim_key: "agent's qualitative note"}
      - panel_insights: "agent's panel-level narrative"
      - great_divide_override: {punchline, bull_say_rounds, bear_say_rounds}
      - narrative_override: {core_conclusion, risks, buy_zones}
      - agent_reviewed: True  (marks that agent has intervened)
    """
    from compute_friendly import compute_scenarios, compute_exit_triggers
    ag = agent_analysis or {}

    basic = (raw.get("dimensions", {}).get("0_basic") or {}).get("data") or {}
    name = basic.get("name") or raw.get("ticker")
    price = basic.get("price") or 0

    # v2.7 · 按股票风格动态加权（解决 "几乎一片回避" 的系统性偏差）
    # detect_style 识别：白马/高成长/周期/小盘投机/分红防御/困境反转/量化因子/中性
    # apply_style_weights：评委组级×个体 override 加权 + 22 维 fundamental dim mult
    # neutral 半权计入 consensus（修正旧公式 0% 权重的问题）
    style_label = "balanced"
    style_diag = {}
    fund_score = dims_scored.get("fundamental_score", 60)
    consensus = panel.get("panel_consensus", 50)
    fund_score_old = fund_score
    consensus_old = consensus
    try:
        from lib.stock_style import detect_style, apply_style_weights, STYLE_LABELS, STYLE_EXPLANATIONS
        # Build feature dict for style detection
        bd = basic
        try:
            mcap_yi = float(bd.get("market_cap_raw") or 0) / 1e8 if bd.get("market_cap_raw") else 0
        except (ValueError, TypeError):
            mcap_yi = 0
        # 简化的局部数字转换（避开 generate_synthesis 内 _f 作用域冲突）
        def _ff(v, dflt=0.0):
            try:
                if v is None or v == "":
                    return dflt
                return float(str(v).replace(",", "").replace("%", "").replace("亿", "").replace("+", "").strip())
            except (ValueError, TypeError):
                return dflt
        d_fin = (dims_scored.get("dimensions", {}).get("1_financials") or {})
        feat_for_style = {
            "code": raw.get("ticker", ""),
            "market": raw.get("market", "A"),
            "industry": bd.get("industry", "") or "",
            "market_cap_yi": mcap_yi,
            "pe": _ff(bd.get("pe_ttm")),
            "pe_ttm": _ff(bd.get("pe_ttm")),
            "pb": _ff(bd.get("pb")),
            "roe_5y_avg": _ff(d_fin.get("roe_5y_avg")),
            "roe_5y_min": _ff(d_fin.get("roe_5y_min")),
            "revenue_growth_3y_cagr": _ff(d_fin.get("revenue_growth_3y_cagr")),
            "dividend_yield": _ff(bd.get("dividend_yield_ttm")),
        }
        style_label = detect_style(feat_for_style, raw)
        adj = apply_style_weights(panel.get("investors", []), dims_scored, style_label)
        fund_score = adj["fundamental_score"]
        consensus = adj["panel_consensus"]
        style_diag = adj["diagnostics"]
        print(f"\n  🎯 v2.7 风格识别: {style_label} ({STYLE_LABELS.get(style_label,'?')}) — fund {fund_score_old:.1f}→{fund_score:.1f} · consensus {consensus_old:.1f}→{consensus:.1f}")
    except Exception as _se:
        print(f"  ⚠️ v2.7 风格加权失败（沿用原始公式）: {type(_se).__name__}: {str(_se)[:120]}")

    overall = fund_score * 0.6 + consensus * 0.4

    # v2.11 · verdict 阈值重校准 · 论坛+微信反馈用户心理及格线是 65 分
    # 调整：85/70/55/40 → 80/65/50/35，让白马/真强股进"可以蹲一蹲"档
    # v3.4.1 · 用户反馈"神剑股份(002361 58分) 和博云新材(002297 60分) verdict 都是观望优先 ·
    #         看不出差异"。50-65 这个 15 分跨度太宽 · 拆成 50-55 / 55-60 / 60-65 三档 ·
    #         同时把流派分歧度作为后缀显示让差异更明显.
    if overall >= 80:
        verdict_label = "Strong Buy"
    elif overall >= 70:
        verdict_label = "Worth Accumulating"
    elif overall >= 65:
        verdict_label = "Worth Accumulating (weak)"
    elif overall >= 60:
        verdict_label = "Watch (lean long)"
    elif overall >= 55:
        verdict_label = "Watch (neutral)"
    elif overall >= 50:
        verdict_label = "Watch (lean short)"
    elif overall >= 35:
        verdict_label = "Cautious"
    else:
        verdict_label = "Avoid"

    # School-divergence suffix so users can see e.g. "5 schools bearish / 2 bullish"
    school_scores = panel.get("school_scores", {})
    if school_scores:
        bullish_schools = [s["label"] for s in school_scores.values()
                          if s.get("verdict") in ("Overweight", "Buy")]
        bearish_schools = [s["label"] for s in school_scores.values()
                          if s.get("verdict") == "Avoid"]
        if bullish_schools and bearish_schools:
            verdict_label += f" · {len(bullish_schools)} schools bullish / {len(bearish_schools)} bearish"
        elif bullish_schools:
            verdict_label += f" · {len(bullish_schools)} schools bullish"
        elif bearish_schools:
            verdict_label += f" · {len(bearish_schools)} schools bearish"

    verdict_detail = f"Fundamentals {fund_score:.1f} · Consensus {consensus:.1f}"

    # Pick bull and bear for great divide
    # CRITICAL: must pick from ACTUALLY bullish/bearish investors, never misattribute
    investors = panel.get("investors", [])

    # v2.6 · 防御性 panel 排序 (fix bug #5: "最看空 27 vs 下面 0 不一致")
    # 非 Claude LLM 可能写出 signal=bullish 但 score=5 这种自相矛盾输出。
    # 旧逻辑按 signal 先分组再选 → 实际可见的最低分(neutral/skip 里 0 分的)反而没被选为 bear。
    # 新逻辑：先排除 skip 和明显异常（score=0 通常是空数据），然后按 score 排序，
    #        bull = 最高分 · bear = 最低分。signal 仅作辅助检查。
    eligible = [
        i for i in investors
        if i.get("signal") != "skip"
        and i.get("score", 0) > 0  # 0 分通常是 fail_msg 幻觉，剔除
    ]
    if not eligible:
        eligible = [i for i in investors if i.get("signal") != "skip"] or investors

    inv_by_score = sorted(eligible, key=lambda x: -x.get("score", 0))
    bull = inv_by_score[0] if inv_by_score else (investors[0] if investors else {})
    bear = inv_by_score[-1] if inv_by_score else (investors[-1] if investors else {})

    # Safety: bull and bear must be different investors
    if bull.get("investor_id") == bear.get("investor_id") and len(inv_by_score) > 1:
        bear = inv_by_score[-2]

    # v2.6 · Sanity warnings: signal vs score 矛盾时打印（不阻断流程）
    def _check_signal_score(inv: dict, role: str) -> None:
        sig = inv.get("signal", "")
        sc = inv.get("score", 50)
        if role == "bull" and sig == "bearish":
            print(f"   ⚠️ Top bull '{inv.get('name')}' signal=bearish but score={sc} → 数据可能错乱")
        if role == "bear" and sig == "bullish":
            print(f"   ⚠️ Bottom bear '{inv.get('name')}' signal=bullish but score={sc} → 数据可能错乱")
    _check_signal_score(bull, "bull")
    _check_signal_score(bear, "bear")

    # Build debate rounds — use actual headline + reasoning from evaluator
    bull_headline = bull.get("headline", bull.get("comment", ""))
    bear_headline = bear.get("headline", bear.get("comment", ""))
    bull_reasoning = bull.get("reasoning", "")
    bear_reasoning = bear.get("reasoning", "")

    bull_pass_rules = bull.get("pass", [])
    bull_fail_rules = bull.get("fail", [])
    bear_pass_rules = bear.get("pass", [])
    bear_fail_rules = bear.get("fail", [])

    # Build debate rounds — agent can override with great_divide_override
    gd_override = ag.get("great_divide_override") or {}
    agent_bull_rounds = gd_override.get("bull_say_rounds") or []
    agent_bear_rounds = gd_override.get("bear_say_rounds") or []

    rounds = [
        {
            "round": 1,
            "bull_say": agent_bull_rounds[0] if len(agent_bull_rounds) > 0 else bull_headline,
            "bear_say": agent_bear_rounds[0] if len(agent_bear_rounds) > 0 else bear_headline,
        },
        {
            "round": 2,
            "bull_say": agent_bull_rounds[1] if len(agent_bull_rounds) > 1 else (" · ".join(r.get("msg", r.get("name", "")) for r in bull_pass_rules[:3]) or "The data supports my call."),
            "bear_say": agent_bear_rounds[1] if len(agent_bear_rounds) > 1 else (" · ".join(r.get("msg", r.get("name", "")) for r in bear_fail_rules[:3]) or "Too many risk points."),
        },
        {
            "round": 3,
            "bull_say": agent_bull_rounds[2] if len(agent_bull_rounds) > 2 else f"On balance, {bull.get('score', 0)}/100 — my stance is unchanged.",
            "bear_say": agent_bear_rounds[2] if len(agent_bear_rounds) > 2 else f"On balance, {bear.get('score', 0)}/100 — risk outweighs reward.",
        },
    ]

    kline = (raw.get("dimensions", {}).get("2_kline") or {}).get("data") or {}
    val = (raw.get("dimensions", {}).get("10_valuation") or {}).get("data") or {}

    # v2.0 · Pull institutional modeling summaries
    d20 = (raw.get("dimensions", {}).get("20_valuation_models") or {}).get("data") or {}
    d21 = (raw.get("dimensions", {}).get("21_research_workflow") or {}).get("data") or {}
    d22 = (raw.get("dimensions", {}).get("22_deep_methods") or {}).get("data") or {}
    dcf_summary = d20.get("summary") or {}
    init_cov = d21.get("initiating_coverage") or {}
    ic_memo = d22.get("ic_memo") or {}
    competitive = d22.get("competitive_analysis") or {}

    # Build punchline with conflict — prefer real conflicts over platitudes
    dcf_sm = dcf_summary.get("dcf_safety_margin_pct", 0) or 0
    lbo_irr = dcf_summary.get("lbo_irr_pct", 0) or 0
    tp = (init_cov.get("headline") or {}).get("target_price") or 0
    upside = (init_cov.get("headline") or {}).get("upside_pct", 0) or 0
    rating = (init_cov.get("headline") or {}).get("rating", "")

    # Punchline: prefer agent override, fallback to script generation
    agent_punchline = gd_override.get("punchline") or ""
    if agent_punchline:
        punchline = agent_punchline
    elif dcf_sm and lbo_irr and abs(dcf_sm) > 10 and lbo_irr > 15:
        if dcf_sm < 0 and lbo_irr > 20:
            punchline = f"DCF says {abs(dcf_sm):.0f}% overvalued, but the LBO test shows a PE buyer could still earn {lbo_irr:.0f}% IRR — an interesting conflict."
        elif dcf_sm > 15 and lbo_irr > 20:
            punchline = f"DCF sees {dcf_sm:.0f}% undervalued, and the LBO IRR of {lbo_irr:.0f}% confirms it — a double bullish signal."
        else:
            punchline = f"Institutional models settle on {rating}, target ${tp} ({upside:+.0f}%), LBO-view IRR {lbo_irr:.0f}%."
    elif tp > 0 and abs(upside) > 5:
        punchline = f"Initiation {rating}, target ${tp}, upside {upside:+.0f}%."
    else:
        punchline = f"{name} · a structural disagreement between historical ROE and current valuation — waiting for direction."

    # Risks: prefer agent-written, fallback to script generation from low-scoring dims
    narrative_override = ag.get("narrative_override") or {}
    agent_risks = narrative_override.get("risks") or []
    risks = list(agent_risks) if agent_risks else []
    if not risks:
        for key, dim in dims_scored["dimensions"].items():
            if dim["score"] <= 4:
                reasons = dim.get("reasons_fail", [])
                if reasons:
                    risks.extend(reasons[:1])
                else:
                    # Use dim name as fallback
                    dim_name = dim.get("name") or dim.get("label") or key
                    risks.append(f"{dim_name} scores low ({dim['score']}/10)")

    # If still empty, generate dynamic risks from actual data instead of hardcoded ones
    if not risks:
        pe_val = features.get("pe", 0) if "features" in dir() else 0
        debt_val = features.get("debt_ratio", 0) if "features" in dir() else 0
        # Use features from extract_features if available
        try:
            _f = extract_features(raw, raw.get("dimensions", {}))
            pe_val = _f.get("pe", 0)
            debt_val = _f.get("debt_ratio", 0)
            roe_min = _f.get("roe_5y_min", 0)
            industry = _f.get("industry", "the sector")
        except Exception:
            pe_val, debt_val, roe_min, industry = 0, 0, 0, "the sector"

        if pe_val > 30:
            risks.append(f"P/E of {pe_val:.0f}x — valuation is rich")
        if debt_val > 50:
            risks.append(f"debt ratio {debt_val:.0f}% — financial leverage is high")
        if roe_min < 5:
            risks.append(f"ROE bottoms at {roe_min:.1f}% — inconsistent profitability")
        risks.append(f"intensifying competition in {industry}")
        risks.append("changes in the macro or policy environment")

    risks = risks[:5]

    # Friendly layer
    scenarios = compute_scenarios(raw, dims_scored)
    exit_triggers = compute_exit_triggers(raw, dims_scored, {})
    similar_stocks = raw.get("similar_stocks", [])

    # Dashboard — core_conclusion: agent override > script
    ytd_return = (kline.get("kline_stats") or {}).get("ytd_return", "—")
    agent_core_conclusion = narrative_override.get("core_conclusion") or ""
    core_conclusion = agent_core_conclusion or f"{name} · {int(overall)}/100 · {verdict_label}. {panel['signal_distribution']['bullish']} of 35 investors bullish, YTD {ytd_return}. {punchline}"

    # v2.2 · dim_commentary: prefer agent-written, fallback to AUTO-SUMMARY (v2.6.1)
    # 关键修复：原 fallback 只生成 "[脚本占位]" 字符串，导致直跑模式下报告里
    # 5/6 定性维度是 missing/占位文字。新版直接把 raw_data 字段综合成实际中文。
    agent_dim_commentary = ag.get("dim_commentary") or {}
    dim_commentary_final: dict[str, str] = {}
    dim_labels = {
        "0_basic": "Basic info",
        "1_financials": "Financials",
        "2_kline": "Price / technicals",
        "3_macro": "Macro backdrop",
        "4_peers": "Peer comparison",
        "5_chain": "Supply chain",
        "6_research": "Analyst research",
        "7_industry": "Industry outlook",
        "8_materials": "Raw materials",
        "10_valuation": "Valuation percentile",
        "11_governance": "Governance",
        "14_moat": "Moat",
        "15_events": "Event-driven",
        "17_sentiment": "Sentiment",
    }
    for dim_key, label in dim_labels.items():
        # Agent-written commentary takes priority
        if dim_key in agent_dim_commentary and agent_dim_commentary[dim_key]:
            dim_commentary_final[dim_key] = agent_dim_commentary[dim_key]
        else:
            dim = (raw.get("dimensions", {}).get(dim_key) or {})
            score_info = dims_scored.get("dimensions", {}).get(dim_key) or {}
            score = score_info.get("score", 0)
            auto = _auto_summarize_dim(dim_key, label, dim, score)
            if auto:
                dim_commentary_final[dim_key] = auto

    # v3.5.0 · 读 UZI_SCHOOL env · 把 lock 编码进 synthesis 让报告层渲染 banner
    try:
        from lib.investor_evaluator import get_locked_school, SCHOOL_LABELS
        _locked = get_locked_school()
        school_lock = {"group": _locked, "label": SCHOOL_LABELS.get(_locked, "")} if _locked else None
    except Exception:
        school_lock = None

    return {
        "ticker": raw["ticker"],
        "name": name,
        "overall_score": round(overall, 1),
        "verdict_label": verdict_label,
        "verdict_detail": verdict_detail,  # v3.4.1 · 基本面/共识精确分 · 区分相近 verdict 段的票
        "fundamental_score": round(fund_score, 1),
        "panel_consensus": round(consensus, 1),
        # v3.5.0 · 用户锁定单一流派视角时 · 告诉报告层渲染 banner
        "school_lock": school_lock,
        # v2.15.4 · 按流派分数也带到 synthesis · 让报告层无须回拉 panel.json
        "school_scores": panel.get("school_scores", {}),
        "dim_commentary": dim_commentary_final,  # agent-written > stub
        "institutional_modeling": {
            "dcf_intrinsic": dcf_summary.get("dcf_intrinsic"),
            "dcf_safety_margin_pct": dcf_summary.get("dcf_safety_margin_pct"),
            "dcf_verdict": dcf_summary.get("dcf_verdict"),
            "lbo_irr_pct": dcf_summary.get("lbo_irr_pct"),
            "lbo_verdict": dcf_summary.get("lbo_verdict"),
            "comps_verdict": dcf_summary.get("comps_verdict"),
            "initiating_rating": (init_cov.get("headline") or {}).get("rating"),
            "target_price": (init_cov.get("headline") or {}).get("target_price"),
            "upside_pct": (init_cov.get("headline") or {}).get("upside_pct"),
            "ic_recommendation": (ic_memo.get("sections", {}).get("I_exec_summary", {}) or {}).get("headline"),
            "bcg_position": (competitive.get("bcg_position") or {}).get("category"),
            "industry_attractiveness": competitive.get("industry_attractiveness_pct"),
        },
        # v2.7 · 风格识别 + 加权诊断（让 HTML 报告显示 + agent 可在 agent_analysis.json 覆盖 style）
        "detected_style": style_label,
        "style_label_cn": (lambda: __import__("lib.stock_style", fromlist=["STYLE_LABELS"]).STYLE_LABELS.get(style_label, "?"))() if style_label else "?",
        "style_explanation": (lambda: __import__("lib.stock_style", fromlist=["STYLE_EXPLANATIONS"]).STYLE_EXPLANATIONS.get(style_label, ""))() if style_label else "",
        "style_diagnostics": style_diag,
        "agent_reviewed": bool(ag.get("agent_reviewed")),
        "panel_insights": ag.get("panel_insights") or "",
        "claude_narrative_stub": {
            "_note": "Fields below have been overwritten by the agent" if ag.get("agent_reviewed") else "Fields below are script-generated placeholders; in Task 4 Claude must rewrite them from the raw data",
            "needs_rewrite": [] if ag.get("agent_reviewed") else [
                "great_divide.punchline", "dashboard.core_conclusion",
                "debate.rounds[*].bull_say", "debate.rounds[*].bear_say",
                "buy_zones.*.rationale", "risks[*]"],
        },
        "debate": {
            "bull": {"investor_id": bull["investor_id"], "name": bull["name"], "group": bull["group"]},
            "bear": {"investor_id": bear["investor_id"], "name": bear["name"], "group": bear["group"]},
            "rounds": rounds,
            "punchline": punchline,
        },
        "great_divide": {
            "bull_avatar": bull["investor_id"],
            "bear_avatar": bear["investor_id"],
            "bull_score": bull["score"],
            "bear_score": bear["score"],
            "bull_signal": bull["signal"],
            "bear_signal": bear["signal"],
            "punchline": punchline,
        },
        "risks": risks,
        "buy_zones": narrative_override.get("buy_zones") or {
            "value": {"price": round(price * 0.85, 2) if price else "—", "rationale": "25th-percentile historical P/E"},
            "growth": {"price": round(price * 0.92, 2) if price else "—", "rationale": "reasonable PEG band"},
            "technical": {"price": round(price * 0.95, 2) if price else "—", "rationale": "MA60 support"},
        },
        "friendly": {
            "scenarios": scenarios,
            "exit_triggers": exit_triggers,
            "similar_stocks": similar_stocks,
        },
        "fund_managers": raw.get("fund_managers", []),
        "dashboard": {
            "core_conclusion": core_conclusion,
            "data_perspective": {
                "trend": f"{kline.get('stage', '—')}",
                "price": f"${price}" if price else "—",
                "volume": "—",
                "chips": kline.get("ma_align", "—"),
            },
            "intelligence": {
                "news": "Recent news + filings collected",
                "risks": risks[:3],
                "catalysts": [
                    e.get("event", "Earnings")[:30]
                    for e in ((d21.get("catalyst_calendar") or {}).get("events") or [])
                    if e.get("impact") in ("high", "medium")
                ][:3] or ["Earnings window", "Industry events"],
            },
            "battle_plan": {
                "entry": f"${round(price * 0.92, 2) if price else '—'}",
                "position": "Start at 50%",
                "stop": f"${round(price * 0.85, 2) if price else '—'}",
                "target": f"${round(price * 1.25, 2) if price else '—'}",
            },
        },
    }

