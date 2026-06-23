"""Renderer registry · dim_key → SectionRenderer (US edition · 15 renderers)."""
from __future__ import annotations

from .basic_header import BasicHeaderRenderer
from .chain import ChainRenderer
from .events import EventsRenderer
from .financials import FinancialsRenderer
from .fund import FundRenderer
from .governance import GovernanceRenderer
from .industry import IndustryRenderer
from .kline import KlineRenderer
from .macro import MacroRenderer
from .materials import MaterialsRenderer
from .moat import MoatRenderer
from .peers import PeersRenderer
from .research import ResearchRenderer
from .sentiment import SentimentRenderer
from .valuation import ValuationRenderer

# China-only renderers removed in the US edition:
#   capital_flow (northbound), futures, policy, lhb (Dragon-Tiger), trap, contests
RENDERER_REGISTRY: dict[str, type] = {
    "0_basic": BasicHeaderRenderer,
    "1_financials": FinancialsRenderer,
    "2_kline": KlineRenderer,
    "3_macro": MacroRenderer,
    "4_peers": PeersRenderer,
    "5_chain": ChainRenderer,
    "6_fund_holders": FundRenderer,
    "6_research": ResearchRenderer,
    "7_industry": IndustryRenderer,
    "8_materials": MaterialsRenderer,
    "10_valuation": ValuationRenderer,
    "11_governance": GovernanceRenderer,
    "14_moat": MoatRenderer,
    "15_events": EventsRenderer,
    "17_sentiment": SentimentRenderer,
}


def get_renderer(dim_key: str):
    """Return a renderer instance for dim_key, or None if not registered."""
    cls = RENDERER_REGISTRY.get(dim_key)
    return cls() if cls else None


def list_renderers() -> list[str]:
    return sorted(RENDERER_REGISTRY.keys())
