"""Data-derived growth: revenue CAGR from filings, and the DCF's growth precedence."""

from assay.data.edgar import parse_company_facts, revenue_cagr
from assay.data.sample import acme_inputs
from assay.models.base import Assumption
from assay.models.dcf import DcfModel


def _annual(end, val, filed):
    return {
        "start": f"{int(end[:4]) - 1}-10-01",
        "end": end,
        "val": val,
        "form": "10-K",
        "filed": filed,
    }


def test_revenue_cagr_is_compound_not_average():
    # 100 -> 121 over two years is 10%/yr compounded, not (21/2)=10.5% average.
    series = [
        _annual("2020-09-30", 100.0, "2020-11-01"),
        _annual("2021-09-30", 110.0, "2021-11-01"),
        _annual("2022-09-30", 121.0, "2022-11-01"),
    ]
    cagr, years = revenue_cagr(series)
    assert years == 2
    assert abs(cagr - 0.10) < 1e-9


def test_revenue_cagr_needs_two_points():
    assert revenue_cagr([_annual("2024-09-28", 100.0, "2024-11-01")]) is None
    assert revenue_cagr([]) is None


def test_parse_suggests_growth_from_revenue_history():
    facts = {
        "entityName": "Grower Co",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "start": "2019-10-01",
                                "end": "2020-09-30",
                                "val": 100_000_000_000,
                                "fy": 2020,
                                "form": "10-K",
                                "filed": "2020-11-01",
                                "accn": "a",
                            },
                            {
                                "start": "2021-10-01",
                                "end": "2022-09-30",
                                "val": 121_000_000_000,
                                "fy": 2022,
                                "form": "10-K",
                                "filed": "2022-11-01",
                                "accn": "c",
                            },
                        ]
                    }
                }
            }
        },
    }
    ci = parse_company_facts(facts, cik=1, ticker="G")
    assert ci.suggested_growth is not None
    assert abs(ci.suggested_growth.value - 0.10) < 1e-9
    assert "CAGR" in ci.suggested_growth.basis


def test_dcf_growth_precedence_override_beats_suggestion():
    inp = acme_inputs()
    inp.suggested_growth = Assumption(
        "growth_10y", "Yearly growth, 10y", 0.08, "percent", "5-yr revenue CAGR 8.0%", "plain"
    )

    # With only a suggestion, the DCF uses it and surfaces its basis.
    suggested_result = DcfModel().value(inp)
    growth_used = next(a for a in suggested_result.assumptions if a.key == "growth_10y")
    assert growth_used.value == 0.08
    assert "CAGR" in growth_used.basis
    assert abs(suggested_result.value.base - DcfModel().per_share(inp, 0.08, 0.025, 0.09)) < 1e-6

    # An explicit override wins over the suggestion.
    overridden = DcfModel().value(inp, {"growth_10y": 0.03})
    growth_used = next(a for a in overridden.assumptions if a.key == "growth_10y")
    assert growth_used.value == 0.03
    assert growth_used.basis == "your override"
