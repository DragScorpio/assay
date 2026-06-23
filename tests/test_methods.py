"""Earnings-power and asset-value methods: the other two legs of the triangulation."""

from assay.models.asset_value import AssetValueModel
from assay.models.base import CompanyInputs
from assay.models.earnings_power import EarningsPowerModel
from assay.provenance import Figure, Source, Tier

_SRC = Source("test", Tier.FILING)


def _fig(value, unit="USD", label="x"):
    return Figure(value, unit, _SRC, label)


def _inputs(**kw):
    base = {"ticker": "T", "shares_outstanding": _fig(100_000_000, "shares", "shares")}
    base.update(kw)
    return CompanyInputs(**base)


def test_epv_capitalizes_after_tax_operating_profit():
    inp = _inputs(
        operating_income=_fig(1_000_000_000, "USD", "EBIT"), net_debt=_fig(0, "USD", "nd")
    )
    result = EarningsPowerModel().value(inp)
    assert result.value is not None
    # NOPAT = 1e9 * (1-0.21); EV = NOPAT / 0.09; per share over 100M shares.
    expected = (1_000_000_000 * 0.79 / 0.09) / 100_000_000
    assert abs(result.value.base - expected) < 1e-6
    assert result.value.low <= result.value.base <= result.value.high


def test_epv_declines_without_operating_income():
    assert EarningsPowerModel().value(_inputs()).declined


def test_asset_value_uses_tangible_book_and_is_a_point():
    inp = _inputs(
        stockholders_equity=_fig(2_000_000_000, "USD", "equity"),
        goodwill=_fig(500_000_000, "USD", "goodwill"),
    )
    result = AssetValueModel().value(inp)
    assert result.value is not None
    # (2.0B equity - 0.5B goodwill) / 100M shares = $15.00, reported as a floor (low == high).
    assert abs(result.value.base - 15.0) < 1e-9
    assert result.value.low == result.value.high == result.value.base


def test_asset_value_declines_without_equity():
    assert AssetValueModel().value(_inputs()).declined
