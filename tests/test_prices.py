"""Price adapter: parse the latest close, and behave sanely when no provider is configured."""

import pytest

from assay.data.prices import _parse_tiingo, latest_price
from assay.provenance import Tier


def test_parse_tiingo_takes_the_latest_close():
    data = [
        {"date": "2026-06-18T00:00:00.000Z", "close": 195.0, "open": 194.0},
        {"date": "2026-06-19T00:00:00.000Z", "close": 201.5, "open": 198.0},
    ]
    fig = _parse_tiingo(data, "AAPL")
    assert fig.value == 201.5
    assert fig.unit == "USD/share"
    assert fig.tier == Tier.MARKET  # a price is a Tier 0 market fact
    assert fig.source.as_of == "2026-06-19"


def test_parse_tiingo_empty_raises():
    with pytest.raises(LookupError):
        _parse_tiingo([], "AAPL")


def test_latest_price_offline_returns_none(monkeypatch):
    monkeypatch.setenv("ASSAY_PRICE_PROVIDER", "offline")
    assert latest_price("AAPL") is None


def test_latest_price_tiingo_without_key_raises(monkeypatch):
    monkeypatch.setenv("ASSAY_PRICE_PROVIDER", "tiingo")
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        latest_price("AAPL")
