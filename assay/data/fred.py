"""FRED adapter (Tier 1) — macro data from the St. Louis Federal Reserve.

Used for the risk-free rate that anchors the discount rate (e.g. the 10-year Treasury, series
``DGS10``). Free API key via ``FRED_API_KEY``:

    https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=...&file_type=json

Implemented in v0.2. Until then the DCF uses its conservative default discount rate.
"""

from __future__ import annotations

import os

OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
RISK_FREE_SERIES = "DGS10"  # 10-year Treasury constant maturity


def risk_free_rate() -> float:
    """Latest risk-free rate as a decimal (e.g. 0.043). Not implemented until v0.2."""
    if not os.environ.get("FRED_API_KEY"):
        raise NotImplementedError("Set FRED_API_KEY; the FRED adapter lands in v0.2.")
    raise NotImplementedError("FRED adapter lands in v0.2.")
