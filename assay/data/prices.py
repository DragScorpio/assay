"""Price adapter (Tier 0): the current market quote.

Reputable providers agree to the cent on liquid US equities, so the choice is about reliability and
licensing, not accuracy. Pick one via ``ASSAY_PRICE_PROVIDER`` and set that provider's key. Tiingo is
wired here (free end-of-day quotes); polygon and alpaca are left as documented stubs. Scraped feeds
like yfinance are fine for a prototype but are not the production spine of a truth tool.

``latest_price`` returns ``None`` when offline (the default), so the report simply omits the price
comparison instead of failing. A configured-but-broken provider raises, and the CLI degrades to a
no-price report with a warning.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx

from ..provenance import Figure, Source, Tier

TIINGO_PRICES_URL = "https://api.tiingo.com/tiingo/daily/{ticker}/prices"


def latest_price(ticker: str, client: Optional[httpx.Client] = None) -> Optional[Figure]:
    """The latest market price as a Tier 0 Figure, or None when no provider is configured."""
    provider = os.environ.get("ASSAY_PRICE_PROVIDER", "offline").lower()
    if provider == "offline":
        return None
    if provider == "tiingo":
        return _tiingo_price(ticker, client)
    raise NotImplementedError(
        f"price provider {provider!r} is not wired yet; v0.2 ships Tiingo. "
        "Set ASSAY_PRICE_PROVIDER=tiingo."
    )


def _tiingo_price(ticker: str, client: Optional[httpx.Client]) -> Figure:
    key = os.environ.get("TIINGO_API_KEY")
    if not key:
        raise RuntimeError("ASSAY_PRICE_PROVIDER=tiingo but TIINGO_API_KEY is not set")
    owns = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        resp = client.get(
            TIINGO_PRICES_URL.format(ticker=ticker),
            headers={"Authorization": f"Token {key}", "Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
    finally:
        if owns:
            client.close()
    return _parse_tiingo(data, ticker)


def _parse_tiingo(data: list[dict], ticker: str) -> Figure:
    """Build a Tier 0 price Figure from Tiingo's daily-prices response. Pure, so it is testable."""
    if not data:
        raise LookupError(f"no price data for {ticker!r} from Tiingo")
    latest = data[-1]
    close = float(latest["close"])
    as_of = str(latest.get("date", ""))[:10]
    source = Source("Tiingo EOD", Tier.MARKET, f"{ticker.upper()} close", as_of)
    return Figure(close, "USD/share", source, "Market price")
