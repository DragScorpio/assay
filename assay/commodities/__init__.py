"""Commodities: valued on their own terms, not as businesses.

A commodity has no cash flow, so there is no DCF. The defensible fundamental anchor is the marginal
cost of production (the floor below which supply contracts and the price tends to recover). Assay
reports that floor against the live spot price and is honest that the premium above it is the
market's story, not a fundamental value.
"""

from .registry import COMMODITIES, Commodity, resolve_commodity

__all__ = ["COMMODITIES", "Commodity", "resolve_commodity"]
