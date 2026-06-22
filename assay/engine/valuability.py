"""Valuability — how much of a company's worth rests on hard data versus narrative.

"Valuable vs un-valuable" is a spectrum, not a switch. This produces the banner at the top of every
report and decides whether Assay should value the company at all or honestly refuse and report only
a floor. The rule is conservative on purpose: no durable cash flow means no intrinsic value, only an
asset floor, and we say so.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models.base import CompanyInputs


@dataclass(frozen=True)
class Valuability:
    level: str  # "HIGH" | "MEDIUM" | "LOW"
    rationale: str


def assess(inputs: CompanyInputs) -> Valuability:
    fcf = inputs.free_cash_flow_ttm
    shares = inputs.shares_outstanding

    if fcf is not None and shares is not None and fcf.value > 0:
        return Valuability(
            "HIGH",
            "Cash-generative with shares outstanding disclosed; the intrinsic value rests on "
            "Tier 0 and Tier 1 data.",
        )
    if shares is not None and (inputs.net_debt is not None or inputs.revenue_ttm is not None):
        return Valuability(
            "MEDIUM",
            "Some fundamentals are present but there is no positive free cash flow; only a "
            "partial, floor-leaning estimate is defensible.",
        )
    return Valuability(
        "LOW",
        "No durable cash flow is available; only an asset floor is defensible and the rest would "
        "be narrative. Assay will not fabricate an intrinsic value.",
    )
