"""The long-run real-price anchor for a consumed commodity.

The cost-of-production floor is the supply side. The demand-side anchor is what the commodity has
actually been worth, in today's dollars, over decades: take a long FRED price history, deflate every
observation by CPI into current dollars, and the average is the real level the price oscillates
around. Spot far above it reads as historically expensive (or a new regime). This is fully
data-driven, no curated number. It assumes mean reversion, which a regime change can break, so the
caller labels it as such.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RealPriceAnchor:
    avg: float  # mean real price in today's dollars, in the commodity's display unit
    low: float  # 25th percentile of the real-price distribution
    high: float  # 75th percentile
    n: int  # number of monthly observations used
    span: str  # e.g. "1986-2026"


def _percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = q * (len(sorted_vals) - 1)
    lo = int(idx)
    frac = idx - lo
    if lo + 1 < len(sorted_vals):
        return sorted_vals[lo] * (1 - frac) + sorted_vals[lo + 1] * frac
    return sorted_vals[lo]


def real_price_anchor(
    price_series: list[tuple[str, float]],
    cpi_series: list[tuple[str, float]],
    unit_factor: float = 1.0,
    min_obs: int = 24,
) -> Optional[RealPriceAnchor]:
    """Deflate a nominal price history to today's dollars by CPI and summarize the real level.

    ``price_series`` and ``cpi_series`` are (date, value) rows sorted ascending (FRED's order).
    ``unit_factor`` converts the FRED price unit into the commodity's display unit.
    """
    if len(price_series) < min_obs or not cpi_series:
        return None
    cpi_by_month = {date[:7]: value for date, value in cpi_series}
    cpi_latest = cpi_series[-1][1]
    if cpi_latest <= 0:
        return None

    reals: list[float] = []
    years: list[str] = []
    for date, price in price_series:
        cpi = cpi_by_month.get(date[:7])
        if cpi is None or cpi <= 0 or price <= 0:
            continue
        reals.append(price * (cpi_latest / cpi) * unit_factor)
        years.append(date[:4])
    if len(reals) < min_obs:
        return None

    ordered = sorted(reals)
    return RealPriceAnchor(
        avg=sum(reals) / len(reals),
        low=_percentile(ordered, 0.25),
        high=_percentile(ordered, 0.75),
        n=len(reals),
        span=f"{years[0]}-{years[-1]}",
    )
