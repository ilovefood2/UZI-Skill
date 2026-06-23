"""Investor jury metadata (US edition) · ID / school / watched-field whitelist / DiceBear seed.

US edition: the China-value (group E) and A-share youzi (group F) schools from the
upstream project have been removed. The jury is now 35 Western / global investors
across schools A, B, C, D, G, H, I. Detailed methodology and scoring logic live in
skills/investor-panel/references/group-{a,b,c,d,g,i}.md.
"""
from __future__ import annotations

# Field whitelist convention — these are dimension keys from dimensions.json.
ALL_DIMS = [f"{i}_" for i in range(20)]

INVESTORS = [
    # ──────────── A: Classic Value ────────────
    {"id": "buffett",   "name": "Warren Buffett",   "en": "Warren Buffett",     "group": "A", "fields": ["1_financials", "10_valuation", "11_governance", "14_moat"], "source": "Berkshire Hathaway Letters", "avatar_seed": "Buffett-Owl-Glasses"},
    {"id": "graham",    "name": "Benjamin Graham",  "en": "Benjamin Graham",    "group": "A", "fields": ["1_financials", "10_valuation"], "source": "The Intelligent Investor (1949)", "avatar_seed": "Graham-Bowtie"},
    {"id": "fisher",    "name": "Philip Fisher",    "en": "Philip Fisher",      "group": "A", "fields": ["1_financials", "4_peers", "11_governance", "14_moat"], "source": "Common Stocks and Uncommon Profits (1958)", "avatar_seed": "Fisher-Pipe"},
    {"id": "munger",    "name": "Charlie Munger",   "en": "Charlie Munger",     "group": "A", "fields": ["1_financials", "10_valuation", "11_governance", "14_moat"], "source": "Poor Charlie's Almanack", "avatar_seed": "Munger-Books"},
    {"id": "templeton", "name": "John Templeton",   "en": "John Templeton",     "group": "A", "fields": ["10_valuation", "3_macro"], "source": "Investing the Templeton Way", "avatar_seed": "Templeton-Globe"},
    {"id": "klarman",   "name": "Seth Klarman",     "en": "Seth Klarman",       "group": "A", "fields": ["10_valuation", "11_governance", "15_events"], "source": "Margin of Safety (1991)", "avatar_seed": "Klarman-Vault"},

    # ──────────── B: Growth + VC ────────────
    {"id": "lynch",     "name": "Peter Lynch",      "en": "Peter Lynch",        "group": "B", "fields": ["1_financials", "7_industry", "10_valuation"], "source": "One Up on Wall Street (1989)", "avatar_seed": "Lynch-Tie"},
    {"id": "oneill",    "name": "William O'Neil",   "en": "William O'Neil",     "group": "B", "fields": ["1_financials", "2_kline", "15_events"], "source": "How to Make Money in Stocks (CANSLIM)", "avatar_seed": "Oneill-Chart"},
    {"id": "thiel",     "name": "Peter Thiel",      "en": "Peter Thiel",        "group": "B", "fields": ["4_peers", "7_industry", "14_moat"], "source": "Zero to One (2014)", "avatar_seed": "Thiel-Suit"},
    {"id": "wood",      "name": "Cathie Wood",      "en": "Cathie Wood",        "group": "B", "fields": ["7_industry", "14_moat"], "source": "ARK Big Ideas Annual", "avatar_seed": "CathieWood-Curls"},
    {"id": "andreessen","name": "Marc Andreessen",  "en": "Marc Andreessen",    "group": "B", "tier": "new_gen", "fields": ["7_industry", "14_moat"], "source": "a16z Blog · Techno-Optimist Manifesto (2023)", "avatar_seed": "Andreessen-Bald"},
    {"id": "gurley",    "name": "Bill Gurley",      "en": "Bill Gurley",        "group": "B", "tier": "new_gen", "fields": ["7_industry", "14_moat", "1_financials"], "source": "Above the Crowd · Benchmark", "avatar_seed": "Gurley-Tall"},
    {"id": "naval",     "name": "Naval Ravikant",   "en": "Naval Ravikant",     "group": "B", "tier": "new_gen", "fields": ["14_moat", "11_governance", "7_industry"], "source": "The Almanack of Naval Ravikant", "avatar_seed": "Naval-Beard"},
    {"id": "gerstner",  "name": "Brad Gerstner",    "en": "Brad Gerstner",      "group": "B", "tier": "new_gen", "fields": ["7_industry", "1_financials", "10_valuation"], "source": "Altimeter Quarterly Letters", "avatar_seed": "Gerstner-Glasses"},
    {"id": "chamath",   "name": "Chamath Palihapitiya","en": "Chamath Palihapitiya","group": "B", "tier": "new_gen", "fields": ["7_industry", "17_sentiment"], "source": "Social Capital Letters / All-In Podcast", "avatar_seed": "Chamath-Vest"},

    # ──────────── C: Macro / Hedge ────────────
    {"id": "soros",     "name": "George Soros",     "en": "George Soros",       "group": "C", "fields": ["3_macro", "17_sentiment"], "source": "The Alchemy of Finance (1987)", "avatar_seed": "Soros-Mustache"},
    {"id": "dalio",     "name": "Ray Dalio",        "en": "Ray Dalio",          "group": "C", "fields": ["3_macro"], "source": "Principles (2017)", "avatar_seed": "Dalio-Suit"},
    {"id": "marks",     "name": "Howard Marks",     "en": "Howard Marks",       "group": "C", "fields": ["10_valuation", "17_sentiment", "3_macro"], "source": "The Most Important Thing", "avatar_seed": "Marks-Memos"},
    {"id": "druck",     "name": "Stanley Druckenmiller","en": "Stanley Druckenmiller","group": "C", "fields": ["3_macro"], "source": "Lost Tree Club Speech 2015", "avatar_seed": "Druckenmiller-Bald"},
    {"id": "robertson", "name": "Julian Robertson", "en": "Julian Robertson",   "group": "C", "fields": ["4_peers", "1_financials"], "source": "Tiger Management Letters", "avatar_seed": "Robertson-Tiger"},
    {"id": "burry",     "name": "Michael Burry",    "en": "Michael Burry",      "group": "C", "tier": "new_gen", "fields": ["3_macro", "10_valuation", "17_sentiment"], "source": "Scion Asset Management 13F + X @michaeljburry", "avatar_seed": "Burry-Plaid"},
    {"id": "chanos",    "name": "Jim Chanos",       "en": "Jim Chanos",         "group": "C", "tier": "new_gen", "fields": ["11_governance", "1_financials"], "source": "Kynikos · 30 Years of Short Selling", "avatar_seed": "Chanos-Suit"},

    # ──────────── D: Technical / Trend ────────────
    {"id": "livermore", "name": "Jesse Livermore",  "en": "Jesse Livermore",    "group": "D", "fields": ["2_kline", "15_events"], "source": "Reminiscences of a Stock Operator (1923)", "avatar_seed": "Livermore-Hat"},
    {"id": "minervini", "name": "Mark Minervini",   "en": "Mark Minervini",     "group": "D", "fields": ["2_kline", "1_financials"], "source": "Trade Like a Stock Market Wizard", "avatar_seed": "Minervini-Trophy"},
    {"id": "darvas",    "name": "Nicolas Darvas",   "en": "Nicolas Darvas",     "group": "D", "fields": ["2_kline"], "source": "How I Made $2,000,000 (1960)", "avatar_seed": "Darvas-Box"},
    {"id": "gann",      "name": "William Gann",     "en": "William Gann",       "group": "D", "fields": ["2_kline"], "source": "Truth of the Stock Tape (1923)", "avatar_seed": "Gann-Square"},

    # ──────────── G: Quant / Systematic ────────────
    {"id": "simons",    "name": "Jim Simons",       "en": "Jim Simons",         "group": "G", "fields": ["2_kline"], "source": "The Man Who Solved the Market", "avatar_seed": "Simons-Beard"},
    {"id": "thorp",     "name": "Ed Thorp",         "en": "Ed Thorp",           "group": "G", "fields": ["10_valuation", "1_financials"], "source": "A Man for All Markets", "avatar_seed": "Thorp-Cards"},
    {"id": "shaw",      "name": "David Shaw",       "en": "David Shaw",         "group": "G", "fields": ["1_financials", "2_kline", "10_valuation"], "source": "More Money Than God (Mallaby)", "avatar_seed": "Shaw-Code"},
    {"id": "asness",    "name": "Cliff Asness",     "en": "Cliff Asness",       "group": "G", "tier": "new_gen", "fields": ["10_valuation", "1_financials", "2_kline"], "source": "AQR Capital · Quality Minus Junk / Value-Momentum-Profitability", "avatar_seed": "Asness-Tweet"},

    # ──────────── H: Tech Leaders / AI CEOs ────────────
    {"id": "jensen_huang", "name": "Jensen Huang",  "en": "Jensen Huang",            "group": "H", "tier": "new_gen", "fields": ["7_industry", "5_chain", "14_moat", "4_peers"], "source": "GTC Keynotes / NVDA Earnings Calls", "avatar_seed": "Jensen-Leather"},
    {"id": "musk",         "name": "Elon Musk",     "en": "Elon Musk",               "group": "H", "tier": "new_gen", "fields": ["7_industry", "14_moat", "15_events"], "source": "TSLA Master Plan / X @elonmusk", "avatar_seed": "Musk-Rocket"},
    {"id": "altman",       "name": "Sam Altman",    "en": "Sam Altman",              "group": "H", "tier": "new_gen", "fields": ["7_industry", "14_moat", "5_chain", "11_governance"], "source": "OpenAI Blog / Y Combinator Posts", "avatar_seed": "Altman-Glasses"},
    {"id": "saylor",       "name": "Michael Saylor","en": "Michael Saylor",          "group": "H", "tier": "new_gen", "fields": ["3_macro", "10_valuation", "17_sentiment"], "source": "MSTR Earnings + X @saylor · BTC Treasury Strategy", "avatar_seed": "Saylor-Bitcoin"},

    # ──────────── I: AI Bottleneck Hunter (standalone) ────────────
    # Serenity (@aleabitoreddit) · former AI research scientist / former RISC-V Foundation
    # member / optical-comms engineer. Methodology: hunt AI supply-chain bottlenecks —
    # not the megacaps, but the hardest-to-replace upstream small caps.
    {"id": "serenity",     "name": "Serenity",      "en": "Serenity (@aleabitoreddit)", "group": "I", "tier": "flagship", "fields": ["5_chain", "7_industry", "14_moat", "15_events"], "source": "serenity-alpha skill / X @aleabitoreddit", "avatar_seed": "Serenity-Chip"},
]


def by_id(investor_id: str) -> dict | None:
    return next((i for i in INVESTORS if i["id"] == investor_id), None)


def by_group(group: str) -> list[dict]:
    return [i for i in INVESTORS if i["group"] == group]


def all_ids() -> list[str]:
    return [i["id"] for i in INVESTORS]


def assert_count() -> None:
    expected = 35  # US edition · schools A/B/C/D/G/H/I (China-value E and youzi F removed)
    assert len(INVESTORS) == expected, f"Expected {expected} investors, got {len(INVESTORS)}"


# Backwards-compat alias
assert_50 = assert_count


if __name__ == "__main__":
    assert_count()
    from collections import Counter
    print("Total:", len(INVESTORS))
    print("By group:", Counter(i["group"] for i in INVESTORS))
