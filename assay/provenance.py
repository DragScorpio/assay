"""Provenance and the data-credibility tiers — the backbone of Assay.

Assay never claims a number is "true." It ranks every number by how hard it is to lie about, and
carries that tier plus its source with the number everywhere it flows. A :class:`Figure` is a value
that knows where it came from; nothing in the engine accepts a bare float, so a Tier 3 rumor can
never silently end up inside a Tier 1 calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

_TIER_LABELS = {
    0: "Market fact",
    1: "Audited disclosure",
    2: "Derived / opinion",
    3: "Noise",
}


class Tier(IntEnum):
    """How much a number can be trusted, by how hard it is to fake. Lower is more credible."""

    MARKET = 0  # traded prices, shares outstanding, dividends paid — nobody fakes a printed trade
    FILING = 1  # forced, audited disclosures: SEC filings, regulator macro (FRED)
    DERIVED = 2  # estimates, ratios, analyst opinion — cross-check only, never a value input
    NOISE = 3  # news tone, pundits, social — excluded from value

    @property
    def label(self) -> str:
        return _TIER_LABELS[int(self)]


@dataclass(frozen=True)
class Source:
    """Where a figure came from, precise enough to re-fetch and audit it."""

    name: str  # e.g. "SEC EDGAR 10-K"
    tier: Tier
    locator: str = ""  # accession no, API URL, FRED series id, or the filing concept/line
    as_of: str = ""  # ISO date the value was filed or observed


@dataclass(frozen=True)
class Figure:
    """A number that knows its tier and source. The engine passes these, never bare floats."""

    value: float
    unit: str  # "USD", "USD/share", "shares", "ratio", "percent"
    source: Source
    label: str = ""  # human label, e.g. "Free cash flow (TTM)"

    @property
    def tier(self) -> Tier:
        return self.source.tier
