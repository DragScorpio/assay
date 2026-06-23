"""A fictional company so ``assay demo`` runs the whole pipeline with no network and no keys.

Numbers are illustrative and tagged with a clearly fictional :class:`~assay.provenance.Source`, so
nothing here can ever be mistaken for real market data. This mirrors the worked example in the
project README and design doc.
"""

from __future__ import annotations

from ..models.base import CompanyInputs
from ..provenance import Figure, Source, Tier

_MARKET = Source("Sample market data (fictional)", Tier.MARKET, "demo", "2026-06-19")
_FILING = Source("Sample 10-Q (fictional)", Tier.FILING, "demo/accession-0000", "2026-06-19")


def acme_inputs() -> CompanyInputs:
    """Acme Components Inc. — a boring, profitable, highly valuable industrial. The easy case."""
    return CompanyInputs(
        ticker="ACME",
        name="Acme Components Inc. (fictional)",
        price=Figure(48.20, "USD/share", _MARKET, "Market price"),
        shares_outstanding=Figure(200_000_000, "shares", _FILING, "Shares outstanding"),
        free_cash_flow_ttm=Figure(520_000_000, "USD", _FILING, "Free cash flow (TTM)"),
        net_debt=Figure(400_000_000, "USD", _FILING, "Net debt"),
        revenue_ttm=Figure(4_000_000_000, "USD", _FILING, "Revenue (TTM)"),
        operating_income=Figure(700_000_000, "USD", _FILING, "Operating income"),
        stockholders_equity=Figure(2_500_000_000, "USD", _FILING, "Stockholders equity"),
    )
