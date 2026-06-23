"""The shared pipeline: report_for honors assumption overrides (what the UI sliders feed in)."""

from assay.data.sample import acme_inputs
from assay.pipeline import report_for


def test_report_for_builds_a_valued_report():
    report = report_for(acme_inputs())
    assert report.primary is not None
    assert report.primary.value is not None


def test_growth_override_raises_value():
    inp = acme_inputs()
    low = report_for(inp, {"growth_10y": 0.02}).primary.value.base
    high = report_for(inp, {"growth_10y": 0.10}).primary.value.base
    assert high > low


def test_discount_rate_override_moves_value_inversely():
    inp = acme_inputs()
    cheaper = report_for(inp, {"wacc": 0.08}).primary.value.base
    dearer = report_for(inp, {"wacc": 0.12}).primary.value.base
    assert cheaper > dearer
