"""The set of commodities Assay knows, each with a Yahoo spot symbol and a cost-of-production floor.

The floor is a curated industry estimate (Tier 2), not primary-source data: there is no clean free
feed for marginal cost of production. The values are the *marginal* (high-cost producer) cost, the
level below which supply contracts, which is the conceptually correct floor and runs higher than the
average producer's cost. They are ballpark figures (~2025), labeled clearly as estimates and updated
by hand. ``monetary`` marks the metals whose price is dominated by store-of-value demand rather than
consumption; for those the floor understates value the most, because their worth is mostly monetary.
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
    production_floor: float  # estimated MARGINAL cost of production, in the same unit
    floor_basis: str  # what the floor is and roughly when, for the provenance locator
    floor_source: str  # who the estimate comes from
    monetary: bool = False  # a store-of-value metal (price mostly above the floor is monetary)


# Floors are approximate MARGINAL-producer cost estimates (~2025), not live data. See module docstring.
COMMODITIES: dict[str, Commodity] = {
    "gold": Commodity(
        "gold",
        "Gold",
        ("gold", "xau", "gc=f"),
        "GC=F",
        "USD/oz",
        1800.0,
        "marginal (high-cost producer) all-in cost, estimate ~2025",
        "World Gold Council / miner AISC",
        monetary=True,
    ),
    "silver": Commodity(
        "silver",
        "Silver",
        ("silver", "xag", "si=f"),
        "SI=F",
        "USD/oz",
        20.0,
        "marginal (high-cost producer) all-in cost, estimate ~2025",
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
        "marginal-barrel breakeven (high-cost producer), estimate ~2025",
        "EIA / shale & oil-sands breakeven",
    ),
    "natgas": Commodity(
        "natgas",
        "Natural gas (Henry Hub)",
        ("natgas", "gas", "ng=f"),
        "NG=F",
        "USD/MMBtu",
        3.0,
        "marginal dry-gas breakeven (high-cost producer), estimate ~2025",
        "EIA / dry-gas breakeven",
    ),
    "copper": Commodity(
        "copper",
        "Copper",
        ("copper", "hg=f"),
        "HG=F",
        "USD/lb",
        4.0,
        "marginal (incentive) cost, estimate ~2025",
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
