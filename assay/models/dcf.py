"""Discounted cash flow — what the business is worth if it grows modestly.

A two-stage model: explicit free-cash-flow growth for ten years, then a perpetuity growing forever
at the long-run economy rate. This is the closest thing finance has to a law of value (John Burr
Williams, 1938): a thing is worth the cash it will produce, discounted for time and risk.

All arithmetic is deterministic and lives here in code. The only judgement calls are the three
:class:`~assay.models.base.Assumption`s (growth, forever-growth, discount rate), which the user can
override. Facts (cash flow, shares, debt) come in as sourced Figures and are never altered.
"""

from __future__ import annotations

from typing import Optional

from .base import Assumption, CompanyInputs, ModelResult, ValueRange

#: Defaults are deliberately conservative and sit near long-run norms. Each is overridable.
DEFAULTS: dict[str, float] = {
    "growth_10y": 0.04,  # explicit-period FCF growth
    "terminal_growth": 0.025,  # ~long-run GDP + inflation; never assume a firm outgrows the economy
    "wacc": 0.09,  # discount rate
}
YEARS = 10
#: How far the low/high band perturbs the two assumptions that move the answer most.
_GROWTH_BAND = 0.02
_WACC_BAND = 0.01


class DcfModel:
    name = "Discounted cash flow"
    plain_question = "Worth if it grows modestly"

    def per_share(
        self,
        inputs: CompanyInputs,
        growth: float,
        terminal_growth: float,
        wacc: float,
        years: int = YEARS,
    ) -> Optional[float]:
        """Intrinsic value per share, or ``None`` if the inputs can't support a DCF.

        Returns ``None`` rather than a fabricated number when free cash flow or share count is
        missing or non-positive, or when the discount rate does not exceed forever-growth (the
        perpetuity would be meaningless). Honest refusal beats a made-up figure.
        """
        fcf = inputs.free_cash_flow_ttm
        shares = inputs.shares_outstanding
        if fcf is None or shares is None or fcf.value <= 0 or shares.value <= 0:
            return None
        if wacc <= terminal_growth:
            return None

        net_debt = inputs.net_debt.value if inputs.net_debt is not None else 0.0

        pv = 0.0
        cash = fcf.value
        for t in range(1, years + 1):
            cash *= 1 + growth
            pv += cash / (1 + wacc) ** t
        terminal_value = cash * (1 + terminal_growth) / (wacc - terminal_growth)
        pv += terminal_value / (1 + wacc) ** years

        equity_value = pv - net_debt
        return equity_value / shares.value

    def value(
        self, inputs: CompanyInputs, assumptions: Optional[dict[str, float]] = None
    ) -> ModelResult:
        overrides = assumptions or {}
        growth_assumption = self._resolve_growth(inputs, overrides)
        growth = growth_assumption.value
        terminal = overrides.get("terminal_growth", DEFAULTS["terminal_growth"])
        wacc = overrides.get("wacc", DEFAULTS["wacc"])

        base = self.per_share(inputs, growth, terminal, wacc)
        if base is None:
            return ModelResult(
                method=self.name,
                plain_question=self.plain_question,
                value=None,
                notes=(
                    "Declined to value: a DCF needs positive free cash flow and shares "
                    "outstanding. This company does not provide them."
                ),
            )

        # The band moves the two assumptions that dominate the answer: growth and the discount rate.
        low = self.per_share(inputs, growth - _GROWTH_BAND, terminal, wacc + _WACC_BAND)
        high = self.per_share(inputs, growth + _GROWTH_BAND, terminal, wacc - _WACC_BAND)
        _vals = sorted(v for v in (low, high) if v is not None)
        lo, hi = (_vals[0], _vals[-1]) if len(_vals) == 2 else (base, base)

        used = [
            growth_assumption,
            Assumption(
                "terminal_growth",
                "Forever-growth",
                terminal,
                "percent",
                "near long-run economy growth",
                "how fast it grows after year 10, kept near the economy's pace",
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
            for f in (inputs.free_cash_flow_ttm, inputs.shares_outstanding, inputs.net_debt)
            if f is not None
        ]
        return ModelResult(
            method=self.name,
            plain_question=self.plain_question,
            value=ValueRange(lo, base, hi),
            assumptions=used,
            inputs=inputs_used,
            notes="Two-stage DCF: explicit growth for 10 years, then a perpetuity at forever-growth.",
        )

    @staticmethod
    def _resolve_growth(inputs: CompanyInputs, overrides: dict[str, float]) -> Assumption:
        """Growth precedence: an explicit user override, else a data-derived suggestion, else the
        conservative default. The returned Assumption carries an honest basis for the report."""
        plain = "how fast yearly cash profit rises over the next decade"
        if "growth_10y" in overrides:
            return Assumption(
                "growth_10y",
                "Yearly growth, 10y",
                overrides["growth_10y"],
                "percent",
                "your override",
                plain,
            )
        if inputs.suggested_growth is not None:
            return inputs.suggested_growth
        return Assumption(
            "growth_10y",
            "Yearly growth, 10y",
            DEFAULTS["growth_10y"],
            "percent",
            "default; not yet computed from filings",
            plain,
        )
