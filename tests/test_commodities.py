"""Commodities: resolution, the honest valuability split, and the report render. No network."""

from assay.commodities.registry import COMMODITIES, resolve_commodity
from assay.commodities.report import CommodityReport, assess_commodity, render_commodity_markdown
from assay.provenance import Figure, Source, Tier


def _figs(commodity, spot_value):
    floor = Figure(commodity.production_floor, commodity.unit, Source("est", Tier.DERIVED), "floor")
    spot = Figure(spot_value, commodity.unit, Source("Yahoo Finance", Tier.MARKET), "Spot price")
    return spot, floor


def test_resolve_by_name_alias_and_symbol():
    assert resolve_commodity("gold").key == "gold"
    assert resolve_commodity("GOLD").key == "gold"  # case-insensitive; shadows the Barrick ticker
    assert resolve_commodity("xau").key == "gold"
    assert resolve_commodity("wti").key == "oil"
    assert resolve_commodity("AAPL") is None


def test_monetary_metal_is_low_valuability():
    gold = COMMODITIES["gold"]
    spot, floor = _figs(gold, gold.production_floor * 2.2)  # trades well above its floor
    val = assess_commodity(gold, spot, floor)
    assert val.level == "LOW"
    assert "monetary" in val.rationale


def test_consumed_commodity_is_medium():
    oil = COMMODITIES["oil"]
    spot, floor = _figs(oil, oil.production_floor * 1.4)
    assert assess_commodity(oil, spot, floor).level == "MEDIUM"


def test_missing_spot_degrades_not_crashes():
    gold = COMMODITIES["gold"]
    floor = Figure(gold.production_floor, gold.unit, Source("est", Tier.DERIVED), "floor")
    report = CommodityReport(gold, None, floor, assess_commodity(gold, None, floor))
    md = render_commodity_markdown(report)
    assert "Could not fetch a spot price" in md


def test_report_shows_floor_premium_and_units():
    gold = COMMODITIES["gold"]
    spot, floor = _figs(gold, gold.production_floor * 2.0)
    report = CommodityReport(gold, spot, floor, assess_commodity(gold, spot, floor))
    md = render_commodity_markdown(report)
    assert "Gold" in md
    assert "/oz" in md  # the unit shows
    assert "+100%" in md  # spot is double the floor
    assert "Tier 2" not in md or "estimate" in md.lower()  # the floor is flagged as an estimate
