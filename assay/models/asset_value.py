"""Asset reproduction value — what it would cost to rebuild the business from scratch today.

The floor under the other methods. For a company with no durable cash flows, this (plus net cash)
is often the *only* defensible number, which is exactly what the valuability gradient leans on when
it refuses to value a narrative stock.

Stub for v0.3: returns an honest "declined" result until balance-sheet line items are wired in from
the EDGAR adapter. It will never emit a fabricated number.
"""

from __future__ import annotations

from typing import Optional

from .base import CompanyInputs, ModelResult


class AssetValueModel:
    name = "Asset reproduction"
    plain_question = "Cost to rebuild the business"

    def value(
        self, inputs: CompanyInputs, assumptions: Optional[dict[str, float]] = None
    ) -> ModelResult:
        return ModelResult(
            method=self.name,
            plain_question=self.plain_question,
            value=None,
            notes="Not implemented yet (v0.3). Will reproduce asset value from balance-sheet lines.",
        )
