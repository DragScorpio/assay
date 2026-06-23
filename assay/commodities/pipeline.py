"""Fetch a commodity's spot price and assemble its report. Spot is keyless via Yahoo."""

from __future__ import annotations

import httpx

from ..data.prices import _yahoo_price
from ..provenance import Figure, Source, Tier
from .registry import Commodity
from .report import CommodityReport, assess_commodity


def value_commodity(commodity: Commodity) -> CommodityReport:
    """Build the report: the curated floor (Tier 2) plus a best-effort live spot price (Tier 0)."""
    floor = Figure(
        commodity.production_floor,
        commodity.unit,
        Source(commodity.floor_source, Tier.DERIVED, commodity.floor_basis),
        "Cost-of-production floor (estimate)",
    )

    spot = None
    try:
        raw = _yahoo_price(commodity.yahoo_symbol, None)
        spot = Figure(
            raw.value,
            commodity.unit,
            Source(
                "Yahoo Finance",
                Tier.MARKET,
                f"{commodity.yahoo_symbol} regularMarketPrice",
                raw.source.as_of,
            ),
            "Spot price",
        )
    except (httpx.HTTPError, LookupError, RuntimeError):
        spot = None  # report degrades to the floor only

    valuability = assess_commodity(commodity, spot, floor)
    return CommodityReport(commodity, spot, floor, valuability)
