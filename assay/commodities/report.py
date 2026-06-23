"""The commodity report: spot price versus the cost-of-production floor and, for a consumed
commodity, the long-run real price, valued honestly.

There is no triangulation the way a company has three cash-flow methods, because a commodity has no
cash flows. Instead the report grounds what it can: the cost-of-production floor (Tier 2 estimate),
the live spot (Tier 0), and for a consumed commodity a long-run real-price anchor (Tier 1, FRED
price history deflated by CPI). It is plain that any premium above these is the market's story.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..engine.valuability import Valuability
from ..provenance import Figure
from .realprice import RealPriceAnchor
from .registry import Commodity


@dataclass
class CommodityReport:
    commodity: Commodity
    spot: Optional[Figure]  # Tier 0, may be None if the quote could not be fetched
    floor: Figure  # Tier 2 cost-of-production estimate
    valuability: Valuability
    real_price: Optional[RealPriceAnchor] = None  # Tier 1, consumed commodities only


def fmt_value(value: float, unit: str) -> str:
    """Format a per-unit price, e.g. $1,300.00/oz or $50.00/bbl."""
    per = unit.replace("USD/", "/")  # "USD/oz" -> "/oz"
    return f"${value:,.2f}{per}"


def fmt_unit(fig: Figure) -> str:
    return fmt_value(fig.value, fig.unit)


def assess_commodity(
    commodity: Commodity,
    spot: Optional[Figure],
    floor: Figure,
    real_price: Optional[RealPriceAnchor] = None,
) -> Valuability:
    """How much of a commodity's price is anchorable versus narrative."""
    if spot is None:
        return Valuability(
            "LOW", "Could not fetch a spot price; only the estimated production floor is available."
        )
    premium = (spot.value - floor.value) / floor.value
    if commodity.monetary:
        return Valuability(
            "LOW",
            f"The floor is only the cost to produce it, not a fair value. Most of {commodity.name}'s "
            f"worth (~{premium * 100:.0f}% above the floor) is monetary: a store of value with no cash "
            "flow, which no arithmetic can price. Assay grounds the floor and is honest that the rest "
            "is monetary conviction, not calculation.",
        )
    if real_price is not None:
        if spot.value > real_price.high:
            stance = "above its long-run real range, so by its own history it is expensive (or in a new regime)"
        elif spot.value < real_price.low:
            stance = "below its long-run real range, so by its own history it is cheap"
        else:
            stance = (
                "within its long-run real range, so it is roughly fairly valued by its own history"
            )
        return Valuability(
            "MEDIUM",
            "A consumed commodity with two grounded anchors: the marginal cost of production and the "
            f"long-run real price. Spot is {stance}. Assay reports the anchors, not a forecast.",
        )
    return Valuability(
        "MEDIUM",
        "A consumed commodity, so the marginal cost of production is a meaningful long-run anchor. "
        f"The price sits {premium * 100:+.0f}% versus the floor and swings with supply and demand; "
        "Assay reports the floor, not a forecast.",
    )


def _real_stance(spot: Figure, real_price: RealPriceAnchor) -> str:
    if spot.value > real_price.high:
        base = "Spot sits above both anchors, so by its own history this is expensive, possibly a new-regime premium."
    elif spot.value < real_price.low:
        base = "Spot sits below its real history, so this is historically cheap."
    else:
        base = "Spot sits within its long-run real range, so it is roughly fairly valued by its own history."
    return (
        base + " (The real-price anchor assumes mean reversion, which a regime change can break.)"
    )


_TIER_NOTE = (
    "Tiers: spot is Tier 0 (a market fact); the long-run real price is Tier 1 (FRED data deflated by "
    "CPI); the cost-of-production floor is Tier 2 (a curated industry estimate, not live data)."
)


def render_commodity_markdown(report: CommodityReport) -> str:
    c = report.commodity
    spot, floor, real_price = report.spot, report.floor, report.real_price

    out = [
        f"# {c.name}: Commodity Value Report",
        "",
        f"**Valuability: {report.valuability.level}.** {report.valuability.rationale}",
        "",
        "### Verdict",
        "",
    ]
    if spot is None:
        out.append(
            f"> Could not fetch a spot price. The estimated cost-of-production floor is about "
            f"{fmt_unit(floor)}."
        )
    elif c.monetary:
        premium = (spot.value - floor.value) / floor.value * 100
        out.append(
            f"> {c.name} trades at {fmt_unit(spot)}. The cost to produce it is about {fmt_unit(floor)}, "
            f"a floor, not a fair value: {c.name} pays no cash, so most of its worth is monetary, a "
            f"store of value that arithmetic cannot price. The price sits {premium:+.0f}% above the "
            "production floor; whether that monetary premium is justified is a question of conviction, "
            "not calculation, and Assay will not fake it."
        )
    elif real_price is not None:
        out.append(
            f"> {c.name} trades at {fmt_unit(spot)}. Two anchors bracket it: the marginal cost of "
            f"production is about {fmt_unit(floor)} (the floor below which supply contracts), and its "
            f"long-run real price, in today's dollars, has averaged {fmt_value(real_price.avg, c.unit)} "
            f"over {real_price.span} (range {fmt_value(real_price.low, c.unit)} to "
            f"{fmt_value(real_price.high, c.unit)}). {_real_stance(spot, real_price)}"
        )
    else:
        premium = (spot.value - floor.value) / floor.value * 100
        out.append(
            f"> {c.name} trades at {fmt_unit(spot)}. The estimated marginal cost of production is about "
            f"{fmt_unit(floor)}, the floor below which supply contracts. The price sits {premium:+.0f}% "
            "above that floor; that premium is supply and demand, which Assay reports but does not "
            "value as a fundamental."
        )

    out += ["", "### Anchors", "", "| What | Value | Tier | Source |", "|---|---|---|---|"]
    if spot is not None:
        loc = f" ({spot.source.locator})" if spot.source.locator else ""
        out.append(
            f"| Spot price | {fmt_unit(spot)} | {int(spot.tier)} ({spot.tier.label}) | "
            f"{spot.source.name}{loc} |"
        )
    if real_price is not None:
        out.append(
            f"| Long-run real price (avg, {real_price.span}) | {fmt_value(real_price.avg, c.unit)} | "
            "1 (FRED data) | FRED price history, deflated by CPI |"
        )
    floor_loc = f" ({floor.source.locator})" if floor.source.locator else ""
    out.append(
        f"| Cost-of-production floor (estimate) | {fmt_unit(floor)} | {int(floor.tier)} "
        f"({floor.tier.label}) | {floor.source.name}{floor_loc} |"
    )

    out += [
        "",
        "### How to read this",
        "",
        "A commodity produces no cash, so it has no intrinsic value the way a business does. Assay "
        "grounds two things where it can: the marginal cost of production (the supply floor) and, for "
        "a consumed commodity, the long-run real price it has averaged in today's dollars (the demand "
        "side). The premium above these is the market's story, not a fundamental value.",
        "",
        _TIER_NOTE,
        "",
        "---",
        "_Assay is not investment advice. It reports reasoned anchors and their provenance._",
    ]
    return "\n".join(out)
