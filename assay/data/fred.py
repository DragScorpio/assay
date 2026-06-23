"""FRED adapter (Tier 1): macro data from the St. Louis Federal Reserve.

Keyless by default. FRED's public CSV download (no API key, no signup) gives the latest risk-free
rate, which we turn into the discount rate: risk-free rate plus an equity risk premium. The FRED API
key is an optional upgrade, never required, and if FRED is unreachable the methods fall back to the
conservative default discount rate.
"""

from __future__ import annotations

from typing import Optional

import httpx

from ..models.base import Assumption

FREDGRAPH_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
RISK_FREE_SERIES = "DGS10"  # 10-year Treasury constant maturity
DEFAULT_EQUITY_RISK_PREMIUM = 0.05  # a standard long-run equity premium


def risk_free_rate(client: Optional[httpx.Client] = None) -> Optional[float]:
    """Latest 10-yr Treasury yield as a decimal (e.g. 0.043), keyless via FRED's public CSV."""
    owns = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        resp = client.get(FREDGRAPH_CSV_URL.format(series=RISK_FREE_SERIES))
        resp.raise_for_status()
        text = resp.text
    finally:
        if owns:
            client.close()
    return _parse_fred_latest(text)


def _parse_fred_latest(text: str) -> Optional[float]:
    """Latest numeric observation from a FRED CSV, percent to decimal. Pure, so it is testable.

    FRED marks missing observations with ".", so we scan from the newest row for the first real value.
    """
    rows = [r for r in text.strip().splitlines() if r.strip()]
    for row in reversed(rows[1:]):  # skip the header line
        parts = row.split(",")
        if len(parts) < 2:
            continue
        raw = parts[1].strip()
        if raw in (".", ""):
            continue
        try:
            return float(raw) / 100.0
        except ValueError:
            continue
    return None


def discount_rate_assumption(
    client: Optional[httpx.Client] = None,
    equity_risk_premium: float = DEFAULT_EQUITY_RISK_PREMIUM,
) -> Optional[Assumption]:
    """A discount-rate Assumption from the live risk-free rate plus an equity risk premium.

    Returns None when the rate cannot be fetched, so callers fall back to the default discount rate.
    """
    rf = risk_free_rate(client)
    if rf is None:
        return None
    rate = rf + equity_risk_premium
    basis = f"10-yr Treasury {rf * 100:.1f}% + {equity_risk_premium * 100:.0f}% equity risk premium"
    return Assumption(
        "wacc",
        "Discount rate",
        rate,
        "percent",
        basis,
        "how hard we shrink future dollars to value them in today's money",
    )
