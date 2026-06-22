"""Earnings power value — what the business is worth if it never grows again.

Bruce Greenwald's method: take normalized, sustainable operating earnings (NOPAT), assume zero
growth, and capitalize them at the discount rate (EPV = NOPAT / WACC). It is a deliberately
conservative anchor that leans on *current* earning power rather than a forecast, so it depends on
far fewer assumptions than a DCF. Comparing EPV to asset value reveals whether the business has a
real competitive advantage (franchise value) or not.

Stub for v0.3: returns an honest "declined" result until normalized operating earnings are wired in
from the EDGAR adapter. It will never emit a fabricated number.
"""

from __future__ import annotations

from typing import Optional

from .base import CompanyInputs, ModelResult


class EarningsPowerModel:
    name = "Earnings power (no growth)"
    plain_question = "Worth if it never grows again"

    def value(
        self, inputs: CompanyInputs, assumptions: Optional[dict[str, float]] = None
    ) -> ModelResult:
        return ModelResult(
            method=self.name,
            plain_question=self.plain_question,
            value=None,
            notes="Not implemented yet (v0.3). Will capitalize normalized NOPAT at the discount rate.",
        )
