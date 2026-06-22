"""Run every valuation method and summarize where they agree.

Triangulation is the truth test: three *independent* methods landing on a similar number is a far
stronger claim than any single one, and where they disagree is itself worth reading. Methods that
honestly decline (``value is None``) are kept in the result so the report can show the refusal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..models.base import CompanyInputs, ModelResult, ValuationModel


@dataclass
class Triangulation:
    results: list[ModelResult]

    @property
    def valued(self) -> list[ModelResult]:
        """Methods that produced a value range."""
        return [r for r in self.results if r.value is not None]

    @property
    def bases(self) -> list[float]:
        return [r.value.base for r in self.valued if r.value is not None]

    @property
    def spread(self) -> Optional[float]:
        """Absolute gap between the highest and lowest base value, or None if nothing valued."""
        b = self.bases
        return (max(b) - min(b)) if b else None

    def converged(self, tol: float = 0.15) -> Optional[bool]:
        """True if every valued method sits within ``tol`` (fractional) of their mean.

        None when fewer than two methods produced a value (nothing to triangulate yet).
        """
        b = self.bases
        if len(b) < 2:
            return None
        mean = sum(b) / len(b)
        if mean == 0:
            return None
        return all(abs(x - mean) / abs(mean) <= tol for x in b)


def triangulate(
    inputs: CompanyInputs,
    models: list[ValuationModel],
    assumptions: Optional[dict[str, float]] = None,
) -> Triangulation:
    """Value ``inputs`` with every method independently. No method sees another's result."""
    return Triangulation([m.value(inputs, assumptions) for m in models])
