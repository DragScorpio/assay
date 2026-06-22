"""The backbone type: tiers are ordered by credibility and travel with the number."""

from assay.provenance import Figure, Source, Tier


def test_tiers_are_ordered_by_credibility():
    assert Tier.MARKET < Tier.FILING < Tier.DERIVED < Tier.NOISE
    assert Tier.MARKET.label == "Market fact"
    assert Tier.FILING.label == "Audited disclosure"


def test_figure_carries_its_tier_and_source():
    src = Source("SEC EDGAR 10-K", Tier.FILING, "accession-123", "2026-01-01")
    fig = Figure(520_000_000, "USD", src, "Free cash flow (TTM)")
    assert fig.tier == Tier.FILING
    assert fig.value == 520_000_000
    assert fig.source.name == "SEC EDGAR 10-K"
