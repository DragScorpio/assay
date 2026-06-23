"""Asset reproduction value — what it would cost to rebuild the business from scratch today.

The floor under the other methods. As a defensible, filing-sourced proxy for reproduction cost,
Assay uses tangible book value: stockholders' equity minus goodwill and other intangibles (the parts
of book value that cannot be rebuilt with cash). For a company with no durable cash flows this floor,
plus net cash, is often the *only* number worth trusting, which is what the valuability gradient
leans on when it refuses to value a narrative stock.

This is a single floor value, not a range, so the result's low and high equal its base.
"""

from __future__ import annotations

from typing import Optional

from .base import CompanyInputs, ModelResult, ValueRange


class AssetValueModel:
    name = "Asset reproduction"
    plain_question = "Cost to rebuild the business"

    def value(
        self, inputs: CompanyInputs, assumptions: Optional[dict[str, float]] = None
    ) -> ModelResult:
        equity = inputs.stockholders_equity
        shares = inputs.shares_outstanding
        if equity is None or shares is None or shares.value <= 0:
            return ModelResult(
                method=self.name,
                plain_question=self.plain_question,
                value=None,
                notes="Declined to value: needs stockholders' equity and shares outstanding.",
            )

        tangible = equity.value
        inputs_used = [equity]
        note = "Book value of equity as an asset-reproduction floor."
        if inputs.goodwill is not None:
            tangible -= inputs.goodwill.value
            inputs_used.append(inputs.goodwill)
        if inputs.intangibles is not None:
            tangible -= inputs.intangibles.value
            inputs_used.append(inputs.intangibles)
        if inputs.goodwill is not None or inputs.intangibles is not None:
            note = "Tangible book value (equity minus goodwill and intangibles) as an asset floor."
        inputs_used.append(shares)

        per_share = tangible / shares.value
        return ModelResult(
            method=self.name,
            plain_question=self.plain_question,
            value=ValueRange(per_share, per_share, per_share),  # a floor, not a range
            inputs=inputs_used,
            notes=note,
        )
