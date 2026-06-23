"""The monetary lens for a store-of-value metal (gold, silver).

A monetary metal pays no cash, so it cannot be valued. But we can place it against its own monetary
history with two relative gauges, both keyless:

- Purchasing power: its price deflated by CPI into today's dollars, and where today sits in that
  distribution. This is the inflation-hedge question.
- Versus the money supply: its price relative to US M2, and where today sits in that distribution.
  This is the dollar-debasement question.

Both are percentiles, not values: high means historically rich by that measure, low means cheap.
They assume the monetary past is a guide, which a reflexive, belief-driven asset can break. Whatever
sits beyond even these is conviction, which Assay refuses to price.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MonetaryLens:
    real_pct: Optional[float]  # % of real-price history below today's price (purchasing power)
    real_span: str  # e.g. "2000-2026"
    m2_pct: Optional[float]  # % of price/M2 history below today's ratio (vs money supply)
    m2_span: str


def _pct_rank(sorted_vals: list[float], x: float) -> float:
    """Percent of values at or below x, in [0, 100]."""
    return 100.0 * bisect.bisect_right(sorted_vals, x) / len(sorted_vals)


def monetary_lens(
    price_history: list[tuple[str, float]],
    cpi_series: list[tuple[str, float]],
    m2_series: list[tuple[str, float]],
    spot_value: float,
    unit_factor: float = 1.0,
    min_obs: int = 60,
) -> Optional[MonetaryLens]:
    """Where today's price sits versus the metal's own real-price and price-vs-M2 history."""
    cpi_by = {d[:7]: v for d, v in cpi_series}
    cpi_latest = cpi_series[-1][1] if cpi_series else None
    reals: list[float] = []
    real_years: list[str] = []
    if cpi_latest:
        for date, price in price_history:
            cpi = cpi_by.get(date[:7])
            if cpi and cpi > 0 and price > 0:
                reals.append(price * (cpi_latest / cpi) * unit_factor)
                real_years.append(date[:4])
    real_pct: Optional[float] = None
    real_span = ""
    if len(reals) >= min_obs:
        real_pct = _pct_rank(sorted(reals), spot_value)
        real_span = f"{real_years[0]}-{real_years[-1]}"

    m2_by = {d[:7]: v for d, v in m2_series}
    m2_latest = m2_series[-1][1] if m2_series else None
    ratios: list[float] = []
    m2_years: list[str] = []
    for date, price in price_history:
        m2 = m2_by.get(date[:7])
        if m2 and m2 > 0 and price > 0:
            ratios.append(price * unit_factor / m2)
            m2_years.append(date[:4])
    m2_pct: Optional[float] = None
    m2_span = ""
    if len(ratios) >= min_obs and m2_latest and m2_latest > 0:
        m2_pct = _pct_rank(sorted(ratios), spot_value * unit_factor / m2_latest)
        m2_span = f"{m2_years[0]}-{m2_years[-1]}"

    if real_pct is None and m2_pct is None:
        return None
    return MonetaryLens(real_pct, real_span, m2_pct, m2_span)
