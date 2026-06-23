"""Price adapter (Tier 0): the current market quote.

Prices are the one piece SEC filings do not provide. To keep Assay usable with no account and no
payment, the default provider is **yahoo**, Yahoo Finance's public chart endpoint, which returns the
quote as JSON with no API key and no signup. It is an unofficial endpoint (it can change and is best
-effort), which is exactly why Tiingo is offered as an optional keyed upgrade for anyone who wants an
official, more stable feed. Either way a price is a Tier 0 market fact and the source is recorded.

An end-of-day or slightly delayed quote is plenty for comparing intrinsic value to what the market
charges; we never need real-time data.

``latest_price`` returns ``None`` only when explicitly set offline, so the report omits the price
comparison instead of failing. A configured-but-broken provider raises, and the CLI degrades to a
no-price report with a warning.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

import httpx

from ..provenance import Figure, Source, Tier

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1d"
YAHOO_HISTORY_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range}&interval={interval}"
)
TIINGO_PRICES_URL = "https://api.tiingo.com/tiingo/daily/{ticker}/prices"

# Yahoo's endpoint rejects requests without a browser-like User-Agent.
_BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def latest_price(ticker: str, client: Optional[httpx.Client] = None) -> Optional[Figure]:
    """The latest market price as a Tier 0 Figure. Defaults to the keyless Yahoo provider."""
    provider = os.environ.get("ASSAY_PRICE_PROVIDER", "yahoo").lower()
    if provider == "offline":
        return None
    if provider == "yahoo":
        return _yahoo_price(ticker, client)
    if provider == "tiingo":
        return _tiingo_price(ticker, client)
    raise NotImplementedError(
        f"price provider {provider!r} is not wired; use 'yahoo' (keyless), 'tiingo', or 'offline'."
    )


# --------------------------------------------------------------------------- Yahoo (keyless default)


def _yahoo_price(ticker: str, client: Optional[httpx.Client]) -> Figure:
    owns = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        resp = client.get(
            YAHOO_CHART_URL.format(ticker=ticker.upper()), headers={"User-Agent": _BROWSER_UA}
        )
        resp.raise_for_status()
        data = resp.json()
    finally:
        if owns:
            client.close()
    return _parse_yahoo(data, ticker)


def _parse_yahoo(data: dict, ticker: str) -> Figure:
    """Build a Tier 0 price Figure from Yahoo's chart JSON. Pure, so it is testable."""
    results = (data.get("chart") or {}).get("result") or []
    if not results:
        raise LookupError(f"no price data for {ticker!r} from Yahoo")
    meta = results[0].get("meta") or {}
    price = meta.get("regularMarketPrice")
    if price is None:
        raise LookupError(f"Yahoo has no quote for {ticker!r}")
    ts = meta.get("regularMarketTime")
    as_of = (
        datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        if isinstance(ts, (int, float))
        else ""
    )
    source = Source("Yahoo Finance", Tier.MARKET, f"{ticker.upper()} regularMarketPrice", as_of)
    return Figure(float(price), "USD/share", source, "Market price")


def yahoo_history(
    symbol: str, range: str = "max", interval: str = "1mo", client: Optional[httpx.Client] = None
) -> list[tuple[str, float]]:
    """Fetch a price history from Yahoo's chart endpoint as [(date, close), ...], keyless."""
    owns = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        resp = client.get(
            YAHOO_HISTORY_URL.format(ticker=symbol, range=range, interval=interval),
            headers={"User-Agent": _BROWSER_UA},
        )
        resp.raise_for_status()
        data = resp.json()
    finally:
        if owns:
            client.close()
    return _parse_yahoo_history(data)


def _parse_yahoo_history(data: dict) -> list[tuple[str, float]]:
    """Parse Yahoo chart JSON into (date, close) rows, skipping null closes. Pure, so it is testable."""
    results = (data.get("chart") or {}).get("result") or []
    if not results:
        return []
    result = results[0]
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    out: list[tuple[str, float]] = []
    for ts, close in zip(timestamps, closes):
        if close is None or not isinstance(ts, (int, float)):
            continue
        date = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        out.append((date, float(close)))
    return out


# --------------------------------------------------------------------------- Tiingo (optional, keyed)


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
