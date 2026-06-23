"""The contract every valuation method implements, plus the value objects that flow through Assay.

Design rule: facts are :class:`~assay.provenance.Figure`s (sourced, tiered, locked). The future is
expressed as :class:`Assumption`s (overridable guesses). A method never invents a fact and never
hides an assumption.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

from ..provenance import Figure


@dataclass(frozen=True)
class Assumption:
    """A forward-looking judgement the user may override. Facts are Figures; guesses are Assumptions."""

    key: str  # machine key, e.g. "growth_10y"
    label: str  # display label, e.g. "Yearly growth, 10y"
    value: float
    unit: str  # "percent", "ratio"
    basis: str  # plain-English reason for this default, e.g. "5-yr revenue CAGR"
    plain: str = ""  # plain-language meaning for a non-expert


@dataclass(frozen=True)
class ValueRange:
    """A per-share value as a range, never false precision. ``base`` is the headline."""

    low: float
    base: float
    high: float
    unit: str = "USD/share"


@dataclass(frozen=True)
class ModelResult:
    """What a valuation method returns.

    ``value is None`` means the method honestly declined to value the company (see ``notes``).
    That is a feature, not an error: some businesses cannot be valued on fundamentals.
    """

    method: str  # "Discounted cash flow"
    plain_question: str  # "Worth if it grows modestly"
    value: Optional[ValueRange]
    assumptions: list[Assumption] = field(default_factory=list)
    inputs: list[Figure] = field(default_factory=list)
    notes: str = ""

    @property
    def declined(self) -> bool:
        return self.value is None


@dataclass
class CompanyInputs:
    """Every primary-source figure a method might need for one company.

    Each field is a :class:`~assay.provenance.Figure` (or ``None`` if unavailable), so provenance
    and tier are preserved all the way into the math. ``figures`` is a generic bag for less-common
    items a future method needs without changing this class.
    """

    ticker: str
    name: str = ""
    price: Optional[Figure] = None  # Tier 0
    shares_outstanding: Optional[Figure] = None  # Tier 0/1
    free_cash_flow_ttm: Optional[Figure] = None  # Tier 1 (cash-flow statement)
    net_debt: Optional[Figure] = None  # Tier 1 (balance sheet)
    revenue_ttm: Optional[Figure] = None  # Tier 1
    operating_income: Optional[Figure] = None  # Tier 1 (EBIT) — for earnings power
    stockholders_equity: Optional[Figure] = None  # Tier 1 (balance sheet) — for asset value
    goodwill: Optional[Figure] = None  # Tier 1, optional — subtracted for tangible book
    intangibles: Optional[Figure] = None  # Tier 1, optional — subtracted for tangible book
    #: A growth assumption derived from the company's own history (e.g. revenue CAGR), if available.
    #: The data layer suggests it; the DCF uses it unless the caller overrides growth explicitly.
    suggested_growth: Optional[Assumption] = None
    figures: dict[str, Figure] = field(default_factory=dict)

    def all_figures(self) -> list[Figure]:
        """Every present Figure, for the provenance ledger."""
        named = [
            self.price,
            self.shares_outstanding,
            self.free_cash_flow_ttm,
            self.net_debt,
            self.revenue_ttm,
            self.operating_income,
            self.stockholders_equity,
            self.goodwill,
            self.intangibles,
        ]
        return [f for f in named if f is not None] + list(self.figures.values())


@runtime_checkable
class ValuationModel(Protocol):
    """The only contract the engine depends on. One method = one class implementing this."""

    name: str
    plain_question: str

    def value(
        self, inputs: CompanyInputs, assumptions: Optional[dict[str, float]] = None
    ) -> ModelResult:
        """Value ``inputs`` under the given assumption overrides (keyed by ``Assumption.key``)."""
        ...
