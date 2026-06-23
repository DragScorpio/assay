"""Fetch a commodity's spot price, then its real-price anchor (consumed) or monetary lens (metal)."""

from __future__ import annotations

import httpx

from ..data.fred import CPI_SERIES, M2_SERIES, fetch_series
from ..data.prices import _yahoo_price, yahoo_history
from ..provenance import Figure, Source, Tier
from .monetary import monetary_lens
from .realprice import real_price_anchor
from .registry import Commodity
from .report import CommodityReport, assess_commodity


def value_commodity(commodity: Commodity) -> CommodityReport:
    """Build the report: the curated floor (Tier 2), a best-effort spot (Tier 0), and either a
    long-run real-price anchor (consumed commodities) or a monetary lens (store-of-value metals)."""
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
        spot = None

    real_price = None
    lens = None
    if commodity.monetary and spot is not None:
        try:
            history = yahoo_history(commodity.yahoo_symbol)
            cpi = fetch_series(CPI_SERIES)
            m2 = fetch_series(M2_SERIES)
            lens = monetary_lens(history, cpi, m2, spot.value, commodity.fred_unit_factor)
        except (httpx.HTTPError, OSError):
            lens = None
    elif commodity.fred_price_series:
        try:
            prices = fetch_series(commodity.fred_price_series)
            cpi = fetch_series(CPI_SERIES)
            real_price = real_price_anchor(prices, cpi, commodity.fred_unit_factor)
        except (httpx.HTTPError, OSError):
            real_price = None

    valuability = assess_commodity(commodity, spot, floor, real_price)
    return CommodityReport(commodity, spot, floor, valuability, real_price, lens)
