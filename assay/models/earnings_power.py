"""Earnings power value — what the business is worth if it never grows again.

Bruce Greenwald's method: take normalized after-tax operating profit (NOPAT) and capitalize it at
the discount rate (EPV = NOPAT / WACC), assuming zero growth. It is a deliberately conservative
anchor that leans on *current* earning power rather than a forecast, so it depends on far fewer
assumptions than a DCF. Comparing EPV to asset value reveals whether the business has a real
competitive advantage (franchise value above its assets) or not.
"""

from __future__ import annotations

from typing import Optional

from .base import Assumption, CompanyInputs, ModelResult, ValueRange

_DEFAULT_TAX = 0.21  # US statutory corporate rate, used as a normalized tax on operating profit
_DEFAULT_WACC = 0.09
_WACC_BAND = 0.01


class EarningsPowerModel:
    name = "Earnings power (no growth)"
    plain_question = "Worth if it never grows again"

    def _per_share(self, inputs: CompanyInputs, tax: float, wacc: float) -> Optional[float]:
        ebit = inputs.operating_income
        shares = inputs.shares_outstanding
        if ebit is None or shares is None or ebit.value <= 0 or shares.value <= 0 or wacc <= 0:
            return None
        nopat = ebit.value * (1 - tax)
        enterprise_value = nopat / wacc
        net_debt = inputs.net_debt.value if inputs.net_debt is not None else 0.0
        return (enterprise_value - net_debt) / shares.value

    def value(
        self, inputs: CompanyInputs, assumptions: Optional[dict[str, float]] = None
    ) -> ModelResult:
        a = assumptions or {}
        tax = a.get("tax_rate", _DEFAULT_TAX)
        wacc = a.get("wacc", _DEFAULT_WACC)

        base = self._per_share(inputs, tax, wacc)
        if base is None:
            return ModelResult(
                method=self.name,
                plain_question=self.plain_question,
                value=None,
                notes="Declined to value: earnings power needs positive operating income and shares.",
            )

        low = self._per_share(inputs, tax, wacc + _WACC_BAND)
        high = self._per_share(inputs, tax, wacc - _WACC_BAND)
        _vals = sorted(v for v in (low, high) if v is not None)
        lo, hi = (_vals[0], _vals[-1]) if len(_vals) == 2 else (base, base)

        used = [
            Assumption(
                "tax_rate",
                "Tax rate",
                tax,
                "percent",
                "US statutory rate (normalized)",
                "tax taken out of operating profit",
            ),
            Assumption(
                "wacc",
                "Discount rate",
                wacc,
                "percent",
                "CAPM: risk-free rate plus a risk premium",
                "how hard we shrink future dollars to value them in today's money",
            ),
        ]
        inputs_used = [
            f
            for f in (inputs.operating_income, inputs.net_debt, inputs.shares_outstanding)
            if f is not None
        ]
        return ModelResult(
            method=self.name,
            plain_question=self.plain_question,
            value=ValueRange(lo, base, hi),
            assumptions=used,
            inputs=inputs_used,
            notes="Normalized after-tax operating profit (NOPAT) capitalized at the discount rate, no growth.",
        )
