"""The commodity report: spot price versus the cost-of-production floor, valued honestly.

There is no triangulation here, because a commodity has no cash flows to value three ways. The report
states the floor (Tier 2 estimate), the live spot price (Tier 0), the premium between them, and a
plain note that the premium is the market's story, not a fundamental value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..engine.valuability import Valuability
from ..provenance import Figure
from .registry import Commodity


@dataclass
class CommodityReport:
    commodity: Commodity
    spot: Optional[Figure]  # Tier 0, may be None if the quote could not be fetched
    floor: Figure  # Tier 2 cost-of-production estimate
    valuability: Valuability


def fmt_unit(fig: Figure) -> str:
    """Format a per-unit price, e.g. $1,300.00/oz or $50.00/bbl."""
    per = fig.unit.replace("USD/", "/")  # "USD/oz" -> "/oz"
    return f"${fig.value:,.2f}{per}"


def assess_commodity(commodity: Commodity, spot: Optional[Figure], floor: Figure) -> Valuability:
    """How much of a commodity's price is anchorable to its production floor versus narrative."""
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
    return Valuability(
        "MEDIUM",
        f"A consumed commodity, so the marginal cost of production is a meaningful long-run anchor. "
        f"The price sits {premium * 100:+.0f}% versus the floor and swings with supply and demand; "
        "Assay reports the floor, not a forecast.",
    )


_TIER_NOTE = (
    "Tiers: spot price is Tier 0 (a market fact); the cost-of-production floor is Tier 2 (a curated "
    "industry estimate, not live data)."
)


def render_commodity_markdown(report: CommodityReport) -> str:
    c = report.commodity
    spot, floor = report.spot, report.floor

    out = [
        f"# {c.name}: Commodity Value Report",
        "",
        f"**Valuability: {report.valuability.level}.** {report.valuability.rationale}",
        "",
        "### Verdict",
        "",
    ]
    if spot is not None:
        premium = (spot.value - floor.value) / floor.value * 100
        if c.monetary:
            out.append(
                f"> {c.name} trades at {fmt_unit(spot)}. The cost to produce it is about "
                f"{fmt_unit(floor)}, a floor, not a fair value: {c.name} pays no cash, so most of its "
                f"worth is monetary, a store of value that arithmetic cannot price. The price sits "
                f"{premium:+.0f}% above the production floor; whether that monetary premium is "
                "justified is a question of conviction, not calculation, and Assay will not fake it."
            )
        else:
            out.append(
                f"> {c.name} trades at {fmt_unit(spot)}. The estimated marginal cost of production is "
                f"about {fmt_unit(floor)}, the floor below which supply contracts. The price sits "
                f"{premium:+.0f}% above that floor; that premium is supply and demand, which Assay "
                "reports but does not value as a fundamental."
            )
    else:
        out.append(
            f"> Could not fetch a spot price. The estimated cost-of-production floor is about "
            f"{fmt_unit(floor)}."
        )

    out += ["", "### Anchor", "", "| What | Value | Tier | Source |", "|---|---|---|---|"]
    if spot is not None:
        loc = f" ({spot.source.locator})" if spot.source.locator else ""
        out.append(
            f"| Spot price | {fmt_unit(spot)} | {int(spot.tier)} ({spot.tier.label}) | "
            f"{spot.source.name}{loc} |"
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
        "A commodity produces no cash, so it has no intrinsic value the way a business does. The most "
        "defensible fundamental anchor is the marginal cost of production: below it, supply contracts "
        "and the price tends to recover. The premium above the floor is the market's story, not a "
        "fundamental value.",
        "",
        _TIER_NOTE,
        "",
        "---",
        "_Assay is not investment advice. It reports a reasoned anchor and its provenance._",
    ]
    return "\n".join(out)
