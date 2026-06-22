"""Data adapters — one per source, each returning tier-tagged :class:`~assay.provenance.Figure`s.

Real sources are documented in :mod:`assay.data.edgar` (Tier 1 filings), :mod:`assay.data.fred`
(Tier 1 macro), :mod:`assay.data.prices` (Tier 0), and :mod:`assay.data.analysts` (Tier 2,
comparison only). :mod:`assay.data.sample` returns a fictional company so the whole pipeline runs
offline with no keys.
"""

from .sample import acme_inputs

__all__ = ["acme_inputs"]
