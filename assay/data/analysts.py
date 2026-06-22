"""Analyst-target adapter (Tier 2) — the market mirror, for comparison only.

These are opinions, never inputs to the value. Assay quotes what analysts *said* (accurately) and
shows it beside the intrinsic range so the user can read the gap. The value is computed first; this
is fetched after and can never feed back into it.

Providers: Financial Modeling Prep or Finnhub (``FMP_API_KEY`` / ``FINNHUB_API_KEY``). v0.3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..provenance import Source


@dataclass(frozen=True)
class AnalystTargets:
    """Consensus price targets. Tier 2 by construction; opinion, not fact."""

    median: float
    low: float
    high: float
    analyst_count: int
    source: Source


def fetch_targets(ticker: str) -> Optional[AnalystTargets]:
    """Consensus analyst targets, or ``None`` when unavailable (e.g. offline). v0.3."""
    return None  # offline default: no analyst data, so the report's market mirror says so
