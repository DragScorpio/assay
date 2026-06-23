"""Live discount rate from FRED's keyless CSV, and that both methods honor it."""

from assay.data.fred import _parse_fred_latest
from assay.data.sample import acme_inputs
from assay.models.base import Assumption
from assay.models.dcf import DcfModel
from assay.models.earnings_power import EarningsPowerModel


def test_parse_fred_latest_percent_to_decimal_skipping_missing():
    csv = "observation_date,DGS10\n2026-06-17,4.25\n2026-06-18,4.30\n2026-06-19,.\n"
    # The newest real value is 4.30%; the final row is a missing observation (".").
    assert abs(_parse_fred_latest(csv) - 0.043) < 1e-9


def test_parse_fred_latest_none_when_empty():
    assert _parse_fred_latest("observation_date,DGS10\n") is None


def test_dcf_uses_suggested_discount_rate():
    inp = acme_inputs()
    inp.suggested_discount_rate = Assumption(
        "wacc",
        "Discount rate",
        0.11,
        "percent",
        "10-yr Treasury 6.0% + 5% equity risk premium",
        "plain",
    )
    result = DcfModel().value(inp)
    wacc = next(a for a in result.assumptions if a.key == "wacc")
    assert wacc.value == 0.11
    assert "Treasury" in wacc.basis
    # acme has no suggested growth, so growth stays at the 4% default; value matches that wacc.
    assert abs(result.value.base - DcfModel().per_share(inp, 0.04, 0.025, 0.11)) < 1e-6


def test_epv_uses_suggested_discount_rate():
    inp = acme_inputs()
    inp.suggested_discount_rate = Assumption(
        "wacc", "Discount rate", 0.10, "percent", "live", "plain"
    )
    wacc = next(a for a in EarningsPowerModel().value(inp).assumptions if a.key == "wacc")
    assert wacc.value == 0.10
