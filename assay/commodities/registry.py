"""The set of commodities Assay knows, each with a Yahoo spot symbol and a cost-of-production floor.

The floor is a curated industry estimate (Tier 2), not primary-source data: there is no clean free
feed for marginal cost of production. The values are ballpark all-in sustaining cost / breakeven
figures, labeled clearly as estimates and updated by hand periodically. ``monetary`` marks the
metals whose price is dominated by store-of-value demand rather than consumption.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Commodity:
    key: str
    name: str
    aliases: tuple[str, ...]
    yahoo_symbol: str  # the futures symbol Yahoo serves a price for, e.g. GC=F
    unit: str  # "USD/oz", "USD/bbl", "USD/MMBtu", "USD/lb"
    production_floor: float  # estimated marginal cost of production, in the same unit
    floor_basis: str  # what the floor is and roughly when, for the provenance locator
    floor_source: str  # who the estimate comes from
    monetary: bool = False  # a store-of-value metal (price mostly above the floor is monetary)


# Floors are approximate industry estimates (~2024), not live data. See module docstring.
COMMODITIES: dict[str, Commodity] = {
    "gold": Commodity(
        "gold",
        "Gold",
        ("gold", "xau", "gc=f"),
        "GC=F",
        "USD/oz",
        1300.0,
        "all-in sustaining cost, industry estimate ~2024",
        "World Gold Council / miner AISC",
        monetary=True,
    ),
    "silver": Commodity(
        "silver",
        "Silver",
        ("silver", "xag", "si=f"),
        "SI=F",
        "USD/oz",
        16.0,
        "all-in sustaining cost, industry estimate ~2024",
        "Primary-silver miner AISC",
        monetary=True,
    ),
    "oil": Commodity(
        "oil",
        "Crude oil (WTI)",
        ("oil", "wti", "crude", "cl=f"),
        "CL=F",
        "USD/bbl",
        50.0,
        "marginal cost of high-cost production, estimate ~2024",
        "EIA / shale & oil-sands breakeven",
    ),
    "natgas": Commodity(
        "natgas",
        "Natural gas (Henry Hub)",
        ("natgas", "gas", "ng=f"),
        "NG=F",
        "USD/MMBtu",
        2.5,
        "marginal cost of dry-gas production, estimate ~2024",
        "EIA / dry-gas breakeven",
    ),
    "copper": Commodity(
        "copper",
        "Copper",
        ("copper", "hg=f"),
        "HG=F",
        "USD/lb",
        3.0,
        "90th-percentile cash cost, estimate ~2024",
        "Industry cost-curve estimate",
    ),
}


def resolve_commodity(query: str) -> Optional[Commodity]:
    """Match a query (name, alias, or symbol) to a known commodity, case-insensitively.

    Note: this shadows the equity ticker GOLD (Barrick); `assay gold` means the metal.
    """
    q = query.strip().lower()
    for commodity in COMMODITIES.values():
        if q == commodity.key or q in commodity.aliases:
            return commodity
    return None
