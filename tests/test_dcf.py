"""The DCF method: values a cash-generative company, refuses without cash flow, responds to overrides."""

from assay.data.sample import acme_inputs
from assay.models.base import CompanyInputs
from assay.models.dcf import DcfModel


def test_values_a_cash_generative_company():
    result = DcfModel().value(acme_inputs())
    assert result.value is not None
    assert result.value.low <= result.value.base <= result.value.high
    assert 30 < result.value.base < 60  # sanity band for the fictional ACME (~$44)
    assert {a.key for a in result.assumptions} == {"growth_10y", "terminal_growth", "wacc"}


def test_declines_without_cash_flow():
    # No fabricated number when the inputs cannot support a DCF.
    result = DcfModel().value(CompanyInputs(ticker="NOCASH"))
    assert result.declined
    assert result.value is None


def test_higher_growth_raises_value():
    base = DcfModel().value(acme_inputs()).value.base
    higher = DcfModel().value(acme_inputs(), {"growth_10y": 0.08}).value.base
    assert higher > base
