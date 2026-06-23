"""Per-investor signature phrases for the evaluation panel (US edition).

Each investor has 3 signal types (bullish/bearish/neutral) and each maps to
2-4 signature lines drawn from their REAL public quotes or methodology.
These are used by run_real_test.py::generate_panel() to produce comments
that actually sound like the person being simulated, not a generic group template.

Keys follow the `id` field in lib/investor_db.py. US edition: the China-value (E)
and A-share youzi (F) schools have been removed; only the 35 Western / global
investors remain.
"""
from __future__ import annotations

# Signature-line templates per investor.
# Variables (filled by run_real_test):
#   {roe}, {pe}, {price}, {name}, {industry}, {growth}, {stage}

PERSONAS: dict[str, dict[str, list[str]]] = {
    # ═══════════════ Group A · Classic Value ═══════════════
    "buffett": {
        "bullish": [
            "Inside our circle of competence, a {roe}% ROE that holds up for years is worth owning for ten.",
            "Price is what you pay, value is what you get. This is a business I'd hold for a decade.",
            "If you wouldn't own it for ten years, don't own it for ten minutes — and this one I'd own.",
        ],
        "bearish": [
            "The ROE and the cash flow both raise questions; this isn't the kind of business we like.",
            "At a P/E of {pe} there's no margin of safety left — I'll wait for others to be fearful.",
            "We don't touch what we can't understand, and I haven't figured out this business model.",
        ],
        "neutral": [
            "I'd want a few more quarters; even a great company needs a fair price.",
            "On the edge of the circle of competence — watch, don't act.",
        ],
    },
    "graham": {
        "bullish": [
            "P/E {pe} and P/B are reasonable, the current ratio passes — it fits the defensive-investor test.",
            "Most of the hard criteria are met; this is a stock that lets me sleep at night.",
            "Long dividend record, stable earnings, undemanding valuation — the three classic value pillars.",
        ],
        "bearish": [
            "P/E × P/B is well past 22.5 — it fails the most basic margin-of-safety test.",
            "I don't see ten straight years of earnings; a defensive portfolio shouldn't touch it.",
            "Short-term the market is a voting machine, and even the voting machine finds this expensive.",
        ],
        "neutral": ["The data is incomplete — I hold the discipline of not buying what doesn't qualify."],
    },
    "fisher": {
        "bullish": [
            "{industry} has real market potential and management is investing in R&D — a promising seedling.",
            "Margins hold, labor relations are stable; most of the 15 points are met.",
            "Scuttlebutt checks out — this name has a good reputation up and down its supply chain.",
        ],
        "bearish": [
            "Management's candor with investors makes me doubt it; I'll wait.",
            "R&D spend isn't enough to support a durable competitive edge.",
        ],
        "neutral": ["I need more scuttlebutt; there isn't enough information yet."],
    },
    "munger": {
        "bullish": [
            "Invert: this business is hard to disrupt and management isn't lying — so it's buyable.",
            "Simple arithmetic — a {roe}% ROE business compounding is just money.",
            "Patience is the investor's great virtue, but this one I've waited on long enough.",
        ],
        "bearish": [
            "Invert — how is this business most likely to die? I can think of a few too many ways.",
            "Psychological bias is at work; when everyone is chasing it, be wary.",
            "If I knew where I'd die I'd never go there — and I can see this one's risk points.",
        ],
        "neutral": ["Better to miss it than to get it wrong."],
    },
    "templeton": {
        "bullish": [
            "P/E is in its historical low zone — this is the point of maximum pessimism to buy.",
            "The market still doubts this name; bull markets are born on pessimism and grow on skepticism.",
            "Against global peers this P/E is already cheap — worth stepping in.",
        ],
        "bearish": [
            "The crowd is getting euphoric, and Templeton's iron rule is to sell into that.",
            "Comparable companies worldwide are cheaper — why buy this one?",
        ],
        "neutral": ["Sentiment hasn't reached extreme pessimism yet; I'll wait for a better price."],
    },
    "klarman": {
        "bullish": [
            "Discount to intrinsic value > 30% — that's the bedrock of the margin of safety.",
            "Downside is contained and the catalyst is visible; Baupost would consider it.",
            "Sentiment is a servant, not a master — right now it's helping me buy cheap.",
        ],
        "bearish": [
            "I don't see a clear catalyst, and the margin of safety isn't enough.",
            "In the worst case this loses 50%; the risk/reward isn't right.",
        ],
        "neutral": ["I'll wait patiently for a more clear-cut opportunity."],
    },

    # ═══════════════ Group B · Growth ═══════════════
    "lynch": {
        "bullish": [
            "PEG is reasonable and the growth story fits on an index card — a classic Fast Grower.",
            "Institutional ownership is still low and insiders are buying; Lynch likes this kind of stock.",
            "Buy what you know. I understand {industry} a little, and I can stalk this one.",
        ],
        "bearish": [
            "PEG is already above 2 — the growth story isn't cheap.",
            "The institutions are all in; there's not much room left to run.",
        ],
        "neutral": ["I haven't fully studied the business — onto the watchlist for now."],
    },
    "oneill": {
        "bullish": [
            "Most of CANSLIM is met: quarterly EPS up 25%+, price near new highs, institutions accumulating.",
            "M (market) up + L (a top-3 industry), six-plus CANSLIM boxes checked — time to go on offense.",
            "The most expensive stocks are often the cheapest — the strong stay strong.",
        ],
        "bearish": [
            "C — quarterly EPS isn't up 25%; it fails CANSLIM on the very first letter.",
            "Price hasn't made new highs and the trend is wrong; I don't buy falling stocks.",
        ],
        "neutral": ["Every CANSLIM letter matters — only 4 of them check out right now."],
    },
    "thiel": {
        "bullish": [
            "{industry} shows monopoly characteristics — this looks 10x better than the #2.",
            "Network effects plus economies of scale — that's the DNA of a great business.",
            "Every great company starts from a secret, and I can see this one's secret.",
        ],
        "bearish": [
            "Fierce competition means this is a loser's game.",
            "I don't see the monopoly gene; the durable advantage is doubtful.",
        ],
        "neutral": ["It hasn't reached the 0 → 1 inflection point yet."],
    },
    "wood": {
        "bullish": [
            "{industry} is at an S-curve inflection, TAM growing >30% a year — buying it is buying the future!",
            "We don't buy stocks, we buy the future. {name} is that future.",
            "The cost curve is falling fast; within 5 years it rewrites the rules of {industry}.",
            "Exponential growth is just starting and most people can't see it — that's when we add.",
            "AI / robotics / energy storage / genomics / blockchain — one of the five platforms, must overweight!",
        ],
        "bearish": [
            "It's not in our five platforms (AI, robotics, storage, blockchain, multiomics) — pass.",
            "Not disruptive enough — an improved version of a legacy industry, not a paradigm shift.",
            "The technology path is uncertain and it hasn't hit the cost-curve inflection — too early.",
        ],
        "neutral": ["The S-curve hasn't inflected yet, but worth tracking — once costs fall 50% we step in."],
    },
    "andreessen": {
        "bullish": [
            "Software is eating {industry}, and {name} is holding the knife. Once network effects lock in, this is the next decade's platform. It's time to build — and to buy.",
            "{name} is founder-mode applied to {industry}: hyper-growth phase, a TAM big enough for a ten-bagger narrative. Techno-optimism, fully loaded.",
        ],
        "bearish": [
            "{industry} is an atoms business, not bits — no software leverage, no zero marginal cost, so {name} can't enter my thesis.",
            "{name} has no network effects and no platform lock-in — it's a feature, not a company. Pass.",
        ],
        "neutral": [
            "{name} touches the edge of software, but the founder hasn't proven they can run the {industry} playbook. Watch list.",
        ],
    },
    "gurley": {
        "bullish": [
            "All revenue is not created equal — {name}'s margin structure tells me this is high-quality revenue and the magnitude of demand in {industry} is real.",
            "{name} looks like the early marketplace winners: positive unit economics, rising repeat rate, controlled burn multiple. I've seen how this ends at Benchmark.",
        ],
        "bearish": [
            "{name}'s EV/Revenue has left orbit. Valuation isn't a badge of honor, it's a liability — the bigger the {industry} hype, the harder these fall.",
            "Unit economics don't pencil out — losing money per order and hoping scale fixes it; nine of ten die in {industry}.",
        ],
        "neutral": [
            "{name}'s demand intensity is okay, but take rate and retention aren't at my confidence level yet. Two more quarters of cohort data.",
        ],
    },
    "naval": {
        "bullish": [
            "{name} has permissionless leverage — code and brand work for it in {industry}. Buy it and sleep; compounding runs itself.",
            "Specific knowledge can't be trained, and {name}'s position in {industry} is that knowledge monetized. Play long-term games.",
        ],
        "bearish": [
            "{name} trades time for money — no leverage, no compounding curve. Seek wealth, not money; this gives neither.",
            "There are no winners in zero-sum games, only survivors. I don't enter the grind that is {industry}.",
        ],
        "neutral": [
            "{name}'s leverage is embryonic, but I can't tell if it'll still be here in ten years. Judgment beats effort — I'll wait.",
        ],
    },
    "gerstner": {
        "bullish": [
            "{name} is on the right side of the AI-capex supercycle: revenue accelerating, not just growing, Rule of 40 cleared with ease. Time to lean in.",
            "We've built the full {industry} model at Altimeter — {name} is the category leader, expensive but the growth supports it. Own the disruptors.",
        ],
        "bearish": [
            "{name}'s growth is downshifting while the valuation is stuck in high gear — that scissor is a classic trim signal.",
            "{industry} isn't on the AI-capex beneficiary chain; {name} won't capture this cycle's beta.",
        ],
        "neutral": [
            "{name}'s Rule of 40 is wobbling near the pass line; next quarter's guidance decides direction. Hold, don't add.",
        ],
    },
    "chamath": {
        "bullish": [
            "Let me tell you why this matters: {name}'s TAM is in the hundreds of billions, and the market is still pricing an exponential curve with linear thinking. Generational opportunity.",
            "{industry} is being rebuilt and {name} holds the blueprint — clear path to profitability, controlled dilution. I'm in.",
        ],
        "bearish": [
            "{name} is a story stock — revenue can't carry the narrative, it runs on slides and hype. I've done SPACs; I know this smell.",
            "With disclosure quality this poor, I won't touch it no matter how hot {industry} is. Transparency or pass.",
        ],
        "neutral": [
            "I buy half of {name}'s thesis: the lane is right, but execution isn't proven. Small position, big patience.",
        ],
    },

    # ═══════════════ Group C · Macro / Hedge ═══════════════
    "soros": {
        "bullish": [
            "Expectations and fundamentals have diverged positively; the reflexive loop is entering its accelerating phase.",
            "The market actively shapes reality — buying now is betting the positive feedback has begun.",
            "I'm rich because I know when I'm wrong — and this time I'm not.",
        ],
        "bearish": [
            "The positive-feedback loop is near its peak; reflexivity is about to reverse.",
            "It's not whether you're right or wrong, it's how much you make when right — the odds aren't enough now.",
        ],
        "neutral": ["The reflexivity signal isn't strong enough yet."],
    },
    "dalio": {
        "bullish": [
            "We're early in the long-term debt cycle, credit conditions are friendly — this asset benefits.",
            "Embrace reality — the data points to buy. Cash is trash and this is an asset.",
            "Pain plus reflection equals progress; the fundamental-turn logic has arrived.",
        ],
        "bearish": [
            "Late debt cycle plus tightening credit — be careful with all risk assets.",
            "In an All-Weather allocation this asset's weight should come down.",
        ],
        "neutral": ["The macro signals are mixed — wait."],
    },
    "marks": {
        "bullish": [
            "The market thermometer is in the fear zone; superior investing comes from buying well, not buying good assets.",
            "I don't pay up for risk, but this time the risk is already priced in.",
            "You can't predict but you can prepare — and now is the time to be prepared.",
        ],
        "bearish": [
            "The thermometer is 80+ and into greed; that's when I choose to step away.",
            "Valuation reverts to the mean eventually — chasing here is paying a tax.",
        ],
        "neutral": ["The temperature is mid-range — stand pat."],
    },
    "druck": {
        "bullish": [
            "The macro liquidity inflection is here, and this kind of name benefits most — worth a concentrated bet.",
            "Always invest in the world 12-18 months out, and this fits the logic of that point.",
            "When you're right, bet big — and now is the time.",
        ],
        "bearish": [
            "Liquidity is still tightening; this valuation can't hold.",
            "I only invest in the world 12-18 months out, and this theme is already stale.",
        ],
        "neutral": ["Not one of my high-conviction names — pass."],
    },
    "robertson": {
        "bullish": [
            "Relatively strongest in {industry} — the Tiger way is to go long the best.",
            "Fundamentals lead the peer group; in a long-best/short-worst book this is the long leg.",
        ],
        "bearish": [
            "Bottom-half of its industry ranking — I might short it to hedge the longs.",
            "Not one I'd buy; we're experts at evaluating companies, not betting the index.",
        ],
        "neutral": ["Mid-pack ranking — no action."],
    },
    "burry": {
        "bullish": [
            "{name}: real assets, real cash flow, nobody looking. What I buy is never the hype — it's the mispriced math.",
            "The market's panic over {industry} created this price. I may be early, but I'm not wrong.",
        ],
        "bearish": [
            "{name}'s valuation only makes sense if 'this time is different' holds. Spoiler: it never has — this is a bubble-basket name.",
            "Insiders selling, retail buying, the {industry} story is on chapter three. I've seen how this movie ends.",
        ],
        "neutral": [
            "{name} isn't cheap enough yet for me to ignore the {industry} cycle risk. Watch. Wait. Reread the filings.",
        ],
    },
    "chanos": {
        "bullish": [
            "Rare: {name}'s cash flow ties to reported earnings and the audit is clean. I don't short honest businesses in {industry} — that itself is a compliment.",
        ],
        "bearish": [
            "{name}'s operating cash flow and net income have diverged for two years — earnings are an opinion, cash is a fact. The Kynikos dogs are barking.",
            "The more active the CEO is in the media, the more I want to see the receivables. {name} is a textbook promotional company.",
        ],
        "neutral": [
            "{name}'s books have no glaring holes yet, but {industry} accounting is elastic — I reserve the right to stay skeptical.",
        ],
    },

    # ═══════════════ Group D · Technical / Trend ═══════════════
    "livermore": {
        "bullish": [
            "A breakout of a key level on supporting volume — the conditions to pyramid in are met.",
            "Money isn't made in the buying and selling, it's made in the waiting — and this time the wait paid off.",
            "The market is always right; the right side is the market's side — buy!",
        ],
        "bearish": [
            "No breakout of the key level and the volume is wrong — no trade.",
            "Never add against the trend.",
        ],
        "neutral": ["Wait for the breakout signal."],
    },
    "minervini": {
        "bullish": [
            "Stage 2 + a VCP contraction + a rising 200-day — with 8 SEPA criteria met, I buy.",
            "I only buy leaders, and this name meets the entire Trend Template.",
            "Relative strength >70, within 25% of the high — a perfect entry setup.",
        ],
        "bearish": [
            "It's not in Stage 2 — I don't touch it.",
            "Only 4 of the Trend Template criteria are met; it fails SEPA discipline.",
            "A stop isn't a suggestion, it's an order — this location doesn't support an entry.",
        ],
        "neutral": ["The technicals aren't in position yet."],
    },
    "darvas": {
        "bullish": [
            "The top of the box broke on volume — a textbook Darvas Box buy point.",
            "A pullback to the box top that holds confirms strength.",
        ],
        "bearish": ["Still chopping inside the box — no direction."],
        "neutral": ["No trade until the box top breaks."],
    },
    "gann": {
        "bullish": [
            "About 55 trading days off the prior low (a Fibonacci window); the angle line supports a long.",
            "The time cycle is in position; price motion follows natural law.",
        ],
        "bearish": ["The time window is entering a high-risk zone."],
        "neutral": ["Time and price haven't resonated."],
    },

    # ═══════════════ Group G · Quant / Systematic ═══════════════
    "simons": {
        "bullish": ["A statistical price anomaly triggers a buy signal — if the model says buy, buy."],
        "bearish": ["The mean-reversion signal shows overbought — trim."],
        "neutral": ["The model has no clear signal."],
    },
    "thorp": {
        "bullish": ["The Kelly criterion gives a positive position size; EV > 0, so bet."],
        "bearish": ["Expected value is negative — don't touch it."],
        "neutral": ["Math doesn't lie — EV is near zero, so no action."],
    },
    "shaw": {
        "bullish": ["The multi-factor score is in the top 20% — quality and momentum both strong."],
        "bearish": ["The multi-factor score is in the bottom 20% — sell across the board."],
        "neutral": ["The factors are mixed — neutral."],
    },
    "asness": {
        "bullish": [
            "{name} lights up on all three of my factors: cheap on value, solid on quality, positive on momentum. That's not an opinion, it's a regression coefficient.",
            "Value and momentum agreeing is rare — {name} is the statistical sweet spot in {industry}. The factor signal says buy.",
        ],
        "bearish": [
            "{name} is a classic lottery ticket: high volatility, negative quality, pure story. The academic literature has one word for its long-run return: bad.",
            "Expensive + poor quality + broken momentum — all three factors negative; {name} is in my short leg.",
        ],
        "neutral": [
            "{name}'s factor signals fight each other: value says buy, momentum says wait. Sin a little — small position or none.",
        ],
    },

    # ═══════════════ Group H · Tech Leaders / AI CEOs ═══════════════
    "jensen_huang": {
        "bullish": [
            "The more you buy, the more you save — {name} sits on a critical link of the AI factory, and the flood of data-center capex is flowing toward it.",
            "Demand in {industry} runs on a light-speed Moore's law, and {name}'s capacity is the entry ticket. We're at the iPhone moment of AI.",
        ],
        "bearish": [
            "{name} isn't in the accelerated-computing world — a general-computing business gets rebuilt in the AI-factory era.",
            "{industry} has no overlap with the AI-compute chain; this isn't a supplier on my radar.",
        ],
        "neutral": [
            "{name} touches the edge of the AI chain but isn't on the qualified list yet. Supply-chain tickets are earned on yield and delivery.",
        ],
    },
    "musk": {
        "bullish": [
            "Break {name} down from first principles: physically sound, the cost curve can be pressed, production is ramping. Production is hard — but they're through the hell.",
            "{industry} needs a vertically integrated maniac, and {name} has that gene.",
        ],
        "bearish": [
            "{name} is a legacy player patching things together in {industry} — from first principles that cost structure shouldn't exist.",
            "I've seen plenty of PowerPoint cars. {name} has no production proof, and physics doesn't lie.",
        ],
        "neutral": [
            "{name}'s direction is right but production hell isn't over. Wait for the next capacity-ramp data.",
        ],
    },
    "altman": {
        "bullish": [
            "{name} sits at a bottleneck of the AGI supply chain — scaling laws still work, and the demand curve for compute and energy only gets steeper.",
            "{industry} is the infrastructure of the intelligence era, and {name}'s position gets repriced repeatedly by the next decade of compute demand.",
        ],
        "bearish": [
            "{name} is pure application layer — the next-gen model could evaporate its moat overnight. Build with the model, not against it.",
            "{industry} isn't on the AGI transmission chain; this wave mostly passes it by.",
        ],
        "neutral": [
            "{name}'s AI narrative holds, but the scaling dividend hasn't hit the financials yet. Cautiously optimistic.",
        ],
    },
    "saylor": {
        "bullish": [
            "{name} holds an asset that appreciates and owes a fiat that depreciates — balance-sheet alchemy for the digital age. There is no second best.",
            "Fiat melts every year, and {name} has found a way to hedge entropy in {industry}. Buy the dip, then buy more.",
        ],
        "bearish": [
            "{name}'s balance sheet is all melting fiat assets with no hard-money exposure — that's saving in ice cubes.",
            "{industry} has no intersection with digital assets; my framework has nothing to say about it.",
        ],
        "neutral": [
            "{name} has a little digital-asset exposure but isn't pure. Half a believer is worse than none — watch.",
        ],
    },

    # ═══════════════ Group I · AI Bottleneck Hunter ═══════════════
    # Serenity (@aleabitoreddit) — voice source: references/serenity-voice.md
    "serenity": {
        "bullish": [
            "{name} sits on the irreplaceable node of {industry} — no substrate, no device. That kind of thing is a money printer, anon. Size it up, then go long.",
            "I reverse-engineered the whole {industry} supply chain, and {name} is the 60%+-share duopoly bottleneck, still grossly mispriced. The market hasn't rotated here — I'm in early.",
            "Everyone stares at the end-market megacaps; I only buy the companies they can't live without. {name} is the chokepoint strait of {industry} — irreplaceable, slow to expand, unpriced. Full size, no apology.",
            "This is a bottleneck of a bottleneck. {name} pins the lifeline of {industry}; everyone downstream has to beg it for supply. Then go long — I'll draw the PT higher.",
        ],
        "bearish": [
            "{name} is trivially replaceable in {industry} — three fabs can supply it. No chokepoint means nothing to me. Pass.",
            "Staring at {name}'s EPS is pointless; it isn't on the {industry} bottleneck, just an ordinary link that can be routed around. No touch.",
            "Supply isn't tight at all — {industry} capacity can ramp anytime, and {name} has zero irreplaceability. I never go long these.",
            "{name} is the hot end-market megacap, not a chokepoint node. A crowded consensus trade — I'd rather watch or even fade it.",
        ],
        "neutral": [
            "{name} might be a potential chokepoint in {industry}, but it isn't hard-confirmed. I'll wait for customer roadmaps and a shortage signal before going long.",
            "{name}'s bottleneck logic is half there — share is concentrated, but whether it can hold capacity is unproven. I want the backlog and ASP from the next earnings call.",
            "The story exists, the mispricing hasn't fully set in. {name}'s position needs confirmation — I'll wait for an institutional-rotation signal and keep a small tracking position until then.",
        ],
    },
}


def get_comment(investor_id: str, signal: str, ctx: dict) -> str:
    """Return a random signature comment for the given investor + signal.
    Substitutes variables from ctx (roe, pe, name, industry, stage, growth, price).
    Falls back to a generic line if investor not registered.
    """
    import random
    entry = PERSONAS.get(investor_id)
    if not entry:
        return _GENERIC_FALLBACK.get(signal, _GENERIC_FALLBACK["neutral"])[0]
    lines = entry.get(signal) or _GENERIC_FALLBACK.get(signal, _GENERIC_FALLBACK["neutral"])
    line = random.choice(lines)
    # Format safely — missing keys fall back to '—'
    try:
        return line.format(**{
            "roe": ctx.get("roe", "—"),
            "pe": ctx.get("pe", "—"),
            "price": ctx.get("price", "—"),
            "name": ctx.get("name", "this stock"),
            "industry": ctx.get("industry", "this industry"),
            "growth": ctx.get("growth", "—"),
            "stage": ctx.get("stage", "—"),
        })
    except (KeyError, IndexError):
        return line


_GENERIC_FALLBACK = {
    "bullish": ["The data supports a buy."],
    "bearish": ["The data doesn't support it."],
    "neutral": ["Watch for now."],
    "skip": ["Outside my circle of competence — no opinion."],
}


def stats() -> dict:
    """Report coverage of PERSONAS — how many investors are registered."""
    return {
        "total": len(PERSONAS),
        "bullish_lines": sum(len(v.get("bullish", [])) for v in PERSONAS.values()),
        "bearish_lines": sum(len(v.get("bearish", [])) for v in PERSONAS.values()),
        "neutral_lines": sum(len(v.get("neutral", [])) for v in PERSONAS.values()),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(stats(), indent=2))
