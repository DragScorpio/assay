"""EDGAR normalization: pick the right XBRL observation and build tier-1 Figures, no network.

The fixture mimics the shape of `data.sec.gov` company-facts: two fiscal years of operating cash
flow (so we can prove the parser takes the latest), capex, cash, debt, shares, and revenue.
"""

from assay.data.edgar import parse_company_facts
from assay.provenance import Tier


def _facts():
    return {
        "entityName": "Test Co Inc.",
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {
                        "shares": [
                            {
                                "end": "2024-09-28",
                                "val": 15_000_000_000,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "accn": "acc-2024",
                            },
                        ]
                    }
                }
            },
            "us-gaap": {
                "NetCashProvidedByUsedInOperatingActivities": {
                    "units": {
                        "USD": [
                            {
                                "start": "2022-10-01",
                                "end": "2023-09-30",
                                "val": 110_000_000_000,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2023-11-01",
                                "accn": "acc-2023",
                            },
                            {
                                "start": "2023-10-01",
                                "end": "2024-09-28",
                                "val": 118_000_000_000,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "accn": "acc-2024",
                            },
                            {
                                "start": "2024-07-01",
                                "end": "2024-09-28",
                                "val": 30_000_000_000,
                                "fy": 2024,
                                "fp": "Q4",
                                "form": "10-Q",
                                "filed": "2024-11-01",
                                "accn": "acc-q",
                            },
                        ]
                    }
                },
                "PaymentsToAcquirePropertyPlantAndEquipment": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-10-01",
                                "end": "2024-09-28",
                                "val": 9_000_000_000,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "accn": "acc-2024",
                            },
                        ]
                    }
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {
                        "USD": [
                            {
                                "end": "2024-09-28",
                                "val": 30_000_000_000,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "accn": "acc-2024",
                            },
                        ]
                    }
                },
                "LongTermDebt": {
                    "units": {
                        "USD": [
                            {
                                "end": "2024-09-28",
                                "val": 100_000_000_000,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "accn": "acc-2024",
                            },
                        ]
                    }
                },
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-10-01",
                                "end": "2024-09-28",
                                "val": 390_000_000_000,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "accn": "acc-2024",
                            },
                        ]
                    }
                },
            },
        },
    }


def test_parses_latest_annual_and_builds_fcf():
    ci = parse_company_facts(_facts(), cik=320193, ticker="TEST")

    assert ci.name == "Test Co Inc."
    assert ci.shares_outstanding.value == 15_000_000_000
    # FCF = latest-annual operating cash flow minus capex, and it takes FY2024 not FY2023.
    assert ci.free_cash_flow_ttm.value == 118_000_000_000 - 9_000_000_000
    assert "2024" in ci.free_cash_flow_ttm.label
    assert ci.net_debt.value == 100_000_000_000 - 30_000_000_000
    assert ci.revenue_ttm.value == 390_000_000_000
    # Everything from filings is tier 1, and price is never sourced from EDGAR.
    assert ci.free_cash_flow_ttm.tier == Tier.FILING
    assert ci.price is None


def test_missing_concepts_degrade_to_none():
    ci = parse_company_facts({"entityName": "Empty", "facts": {}}, cik=1, ticker="X")
    assert ci.free_cash_flow_ttm is None
    assert ci.shares_outstanding is None
    assert ci.net_debt is None
    assert ci.operating_income is None
    assert ci.stockholders_equity is None


def test_parses_operating_income_and_equity_for_the_other_methods():
    facts = {
        "entityName": "Methods Co",
        "facts": {
            "us-gaap": {
                "OperatingIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-10-01",
                                "end": "2024-09-28",
                                "val": 120_000_000_000,
                                "fy": 2024,
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "accn": "a",
                            },
                        ]
                    }
                },
                "StockholdersEquity": {
                    "units": {
                        "USD": [
                            {
                                "end": "2024-09-28",
                                "val": 57_000_000_000,
                                "fy": 2024,
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "accn": "a",
                            },
                        ]
                    }
                },
            }
        },
    }
    ci = parse_company_facts(facts, cik=1, ticker="X")
    assert ci.operating_income.value == 120_000_000_000
    assert ci.stockholders_equity.value == 57_000_000_000


def test_prefers_latest_period_across_candidate_tags():
    # A filer abandoned `Revenues` (2018) for `RevenueFromContract...` (2024). Take the fresh one.
    facts = {
        "entityName": "TagSwitch Co",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "start": "2017-10-01",
                                "end": "2018-09-29",
                                "val": 265_000_000_000,
                                "fy": 2018,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2018-11-05",
                                "accn": "old",
                            },
                        ]
                    }
                },
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-10-01",
                                "end": "2024-09-28",
                                "val": 391_000_000_000,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "accn": "new",
                            },
                        ]
                    }
                },
            }
        },
    }
    ci = parse_company_facts(facts, cik=1, ticker="T")
    assert ci.revenue_ttm.value == 391_000_000_000
    assert "2024" in ci.revenue_ttm.label
