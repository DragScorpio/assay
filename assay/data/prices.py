"""Price adapter (Tier 0) — the current and historical quote.

Reputable providers agree to the cent on liquid US equities, so the choice is about reliability and
licensing, not accuracy. Pick one via ``ASSAY_PRICE_PROVIDER`` (polygon | tiingo | alpaca) and set
that provider's key. Note: scraped/unofficial feeds (e.g. ``yfinance``) are fine for a throwaway
prototype but are not the production spine of a truth tool.

Implemented in v0.2.
"""

from __future__ import annotations

import os

from ..provenance import Figure


def latest_price(ticker: str) -> Figure:
    """Latest market price as a Tier 0 Figure. Not implemented until v0.2."""
    provider = os.environ.get("ASSAY_PRICE_PROVIDER", "offline")
    raise NotImplementedError(
        f"Price provider {provider!r} not wired yet; the price adapter lands in v0.2."
    )
