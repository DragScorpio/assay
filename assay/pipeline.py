"""The shared "gather then value" pipeline used by both the CLI and the UI.

``load_inputs`` does the network work (EDGAR filings, a market price, a live discount rate) and
degrades gracefully if a non-essential source is down. ``report_for`` is pure given the inputs:
triangulate, score valuability, and assemble the layered report under optional assumption overrides.
The overrides are exactly what the UI sliders feed in.
"""

from __future__ import annotations

from typing import Optional

import httpx

from .data.analysts import fetch_targets
from .data.edgar import fetch_company_inputs
from .data.fred import discount_rate_assumption
from .data.prices import latest_price
from .engine.report import Report, build_report
from .engine.triangulate import triangulate
from .engine.valuability import assess
from .models import DEFAULT_MODELS
from .models.base import CompanyInputs

_BEST_EFFORT = (httpx.HTTPError, NotImplementedError, RuntimeError, LookupError)


def load_inputs(ticker: str) -> CompanyInputs:
    """Fetch filings, then best-effort attach a market price and a live discount rate.

    The filings fetch is required, so a LookupError for an unknown ticker propagates. The price and
    discount rate are best-effort: if a source is down, the report just uses what it has.
    """
    inputs = fetch_company_inputs(ticker)
    try:
        price = latest_price(ticker)
        if price is not None:
            inputs.price = price
    except _BEST_EFFORT:
        pass
    try:
        rate = discount_rate_assumption()
        if rate is not None:
            inputs.suggested_discount_rate = rate
    except _BEST_EFFORT:
        pass
    return inputs


def report_for(inputs: CompanyInputs, overrides: Optional[dict[str, float]] = None) -> Report:
    """Triangulate, score valuability, and assemble the report under optional assumption overrides."""
    triangulation = triangulate(inputs, DEFAULT_MODELS, overrides)
    valuability = assess(inputs)
    analyst = fetch_targets(inputs.ticker)
    return build_report(inputs, triangulation, valuability, analyst)
