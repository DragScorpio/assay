"""Assemble and render the layered report — the deterministic spine of Assay.

Every number here comes from sourced Figures and the valuation methods; nothing is invented. The
report renders to Markdown with no LLM and no network. :func:`build_report` also collects the set of
numbers that legitimately appear, so the optional narrator can be checked against it (a model may
only restate numbers the math produced).

Layers: 0 Verdict, 1 Triangulation, 2 Derivation, 3 Assumptions, 4 Market mirror, plus a valuability
banner, a provenance ledger, and the tier legend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..data.analysts import AnalystTargets
from ..models.base import CompanyInputs, ModelResult
from ..models.dcf import DEFAULTS as DCF_DEFAULTS
from ..models.dcf import DcfModel
from .triangulate import Triangulation
from .valuability import Valuability

#: Growth points (decimal) shown in the Layer 3 sensitivity table.
_SENSITIVITY_GROWTHS = [0.02, 0.04, 0.06, 0.08]


# --------------------------------------------------------------------------- formatting helpers


def fmt_money(v: float) -> str:
    """Compact money: $1.2B, $520M, or $4,000."""
    av = abs(v)
    if av >= 1e9:
        return f"${v / 1e9:.1f}B"
    if av >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v:,.0f}"


def fmt_share(v: float) -> str:
    return f"${v:.2f}"


def fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def fmt_figure(fig) -> str:
    """Format a Figure for display, respecting its unit (dollars, per-share, share count, percent)."""
    v = fig.value
    if fig.unit == "USD/share":
        return fmt_share(v)
    if fig.unit == "shares":
        if abs(v) >= 1e9:
            return f"{v / 1e9:.1f}B shares"
        if abs(v) >= 1e6:
            return f"{v / 1e6:.0f}M shares"
        return f"{v:,.0f} shares"
    if fig.unit == "percent":
        return fmt_pct(v)
    return fmt_money(v)


# --------------------------------------------------------------------------- the report object


@dataclass
class Report:
    inputs: CompanyInputs
    triangulation: Triangulation
    valuability: Valuability
    analyst: Optional[AnalystTargets]
    primary: Optional[ModelResult]  # the method used for the headline (DCF when available)
    sensitivity: list[tuple[float, float]]  # (growth, per-share value)
    allowed: set[float] = field(default_factory=set)  # numbers the narrator may restate


def _variants(v: float) -> set[float]:
    """A value at a few roundings, so '$43.91', '$43.9' and '$44' all count as the same number."""
    return {round(v, 2), round(v, 1), round(v, 0)}


def _collect_allowed(report: Report) -> set[float]:
    """Every number that legitimately appears, with rounding variants, for the grounding guard."""
    allowed: set[float] = set()

    for fig in report.inputs.all_figures():
        allowed |= _variants(fig.value)
        allowed |= _variants(fig.value / 1e6)  # the $M rendering
        allowed |= _variants(fig.value / 1e9)  # the $B rendering

    if report.primary is not None and report.primary.value is not None:
        r = report.primary.value
        for x in (r.low, r.base, r.high):
            allowed |= _variants(x)
        for a in report.primary.assumptions:
            allowed |= _variants(a.value * 100)  # percents

    for growth, ps in report.sensitivity:
        allowed |= _variants(growth * 100)
        allowed |= _variants(ps)

    if report.analyst is not None:
        for x in (report.analyst.median, report.analyst.low, report.analyst.high):
            allowed |= _variants(x)
        allowed.add(float(report.analyst.analyst_count))

    return allowed


def build_report(
    inputs: CompanyInputs,
    triangulation: Triangulation,
    valuability: Valuability,
    analyst: Optional[AnalystTargets] = None,
) -> Report:
    """Assemble the report: pick the headline method, compute the sensitivity, collect grounded numbers."""
    # Headline = the DCF result if it produced a value, else the first method that did.
    primary: Optional[ModelResult] = None
    for r in triangulation.valued:
        if r.method == DcfModel.name:
            primary = r
            break
    if primary is None and triangulation.valued:
        primary = triangulation.valued[0]

    # Sensitivity: vary growth, hold the other assumptions at their defaults. DCF only.
    sensitivity: list[tuple[float, float]] = []
    if primary is not None and primary.method == DcfModel.name:
        dcf = DcfModel()
        for g in _SENSITIVITY_GROWTHS:
            ps = dcf.per_share(inputs, g, DCF_DEFAULTS["terminal_growth"], DCF_DEFAULTS["wacc"])
            if ps is not None:
                sensitivity.append((g, ps))

    report = Report(inputs, triangulation, valuability, analyst, primary, sensitivity)
    report.allowed = _collect_allowed(report)
    return report


# --------------------------------------------------------------------------- markdown rendering


_TIER_LEGEND = (
    "| Tier | Name | What it is | Trust |\n"
    "|---|---|---|---|\n"
    "| **0** | Market fact | traded prices, shares, dividends paid | highest |\n"
    "| **1** | Audited disclosure | SEC filings, regulator macro (FRED) | high |\n"
    "| **2** | Derived / opinion | ratios, analyst estimates and targets | cross-check only |\n"
    "| **3** | Noise | news tone, pundits, social | excluded from value |"
)


def _verdict_sentence(report: Report) -> str:
    inp = report.inputs
    price = inp.price
    if report.primary is None or report.primary.value is None:
        return (
            f"Assay declined to assign {inp.name or inp.ticker} an intrinsic value on fundamentals. "
            f"See the valuability note above."
        )
    r = report.primary.value
    parts = [
        f"Under the stated assumptions, {inp.name or inp.ticker} is worth "
        f"{fmt_share(r.low)} to {fmt_share(r.high)} per share (base {fmt_share(r.base)})."
    ]
    if price is not None:
        parts.append(f"The market pays {fmt_share(price.value)}.")
        if price.value > r.high:
            parts.append(
                "The price sits above every method's range, so the market is pricing in more "
                "growth than the cash flows currently show."
            )
        elif price.value < r.low:
            parts.append(
                "The price sits below the range, so the market may be discounting the cash flows."
            )
        else:
            parts.append("The price sits inside the range.")
    parts.append("The gap rides most on one assumption: long-run growth.")
    return " ".join(parts)


def _triangulation_table(report: Report) -> str:
    lines = [
        "| Method | What it answers | Value/share |",
        "|---|---|---|",
    ]
    for r in report.triangulation.results:
        if r.value is not None:
            val = f"{fmt_share(r.value.low)} to {fmt_share(r.value.high)} (base {fmt_share(r.value.base)})"
        else:
            val = "_declined_"
        lines.append(f"| {r.method} | {r.plain_question} | {val} |")
    price = report.inputs.price
    if price is not None:
        lines.append(
            f"| _Market price (ref)_ | What the crowd pays now | _{fmt_share(price.value)}_ |"
        )
    return "\n".join(lines)


def _derivation_block(report: Report) -> str:
    r = report.primary
    if r is None or r.value is None:
        return "_No method produced a value; nothing to derive._"
    lines = [f"**{r.method}**. {r.notes}", "", "Inputs:"]
    for f in r.inputs:
        lines.append(
            f"- {f.label or 'figure'}: {fmt_figure(f)}  ·  Tier {int(f.tier)} ({f.source.name})"
        )
    lines.append("")
    lines.append(
        f"Result: **{fmt_share(r.value.base)}** per share "
        f"(range {fmt_share(r.value.low)} to {fmt_share(r.value.high)})."
    )
    return "\n".join(lines)


def _assumptions_block(report: Report) -> str:
    r = report.primary
    if r is None or not r.assumptions:
        return "_No adjustable assumptions for the headline method._"
    lines = [
        "These are the only judgement calls. Facts above are locked; override only if you have a view.",
        "",
        "| Assumption | Plain meaning | Base (and why) |",
        "|---|---|---|",
    ]
    for a in r.assumptions:
        lines.append(f"| {a.label} | {a.plain} | {fmt_pct(a.value)} ({a.basis}) |")
    if report.sensitivity:
        lines.append("")
        header = "| Growth | " + " | ".join(fmt_pct(g) for g, _ in report.sensitivity) + " |"
        sep = "|---|" + "---|" * len(report.sensitivity)
        row = "| Value/share | " + " | ".join(fmt_share(ps) for _, ps in report.sensitivity) + " |"
        lines += [
            "**Sensitivity (growth to value, other assumptions held):**",
            "",
            header,
            sep,
            row,
        ]
    return "\n".join(lines)


def _market_mirror_block(report: Report) -> str:
    a = report.analyst
    if a is None:
        return (
            "_No analyst data (offline)._ When configured, consensus targets appear here as a "
            "Tier 2 comparison, computed after the value above and never fed into it."
        )
    lines = [
        "Reference only. Tier 2, opinion-laden. Computed after the value above, never an input to it.",
        "",
        "| Reference | Value |",
        "|---|---|",
        f"| Analyst target, median | {fmt_share(a.median)} |",
        f"| Analyst target, low to high | {fmt_share(a.low)} to {fmt_share(a.high)} |",
    ]
    if report.primary is not None and report.primary.value is not None:
        base = report.primary.value.base
        gap = (a.median - base) / base * 100 if base else 0.0
        lines.append(f"| Our intrinsic base | {fmt_share(base)} |")
        lines.append(f"| Gap, median vs our base | {gap:+.0f}% |")
    return "\n".join(lines)


def _ledger_block(report: Report) -> str:
    lines = ["| Figure | Value | Tier | Source |", "|---|---|---|---|"]
    for f in report.inputs.all_figures():
        loc = f" ({f.source.locator})" if f.source.locator else ""
        lines.append(
            f"| {f.label or 'figure'} | {fmt_figure(f)} | {int(f.tier)} ({f.tier.label}) | "
            f"{f.source.name}{loc} |"
        )
    return "\n".join(lines)


def render_markdown(report: Report) -> str:
    inp = report.inputs
    title = inp.name or inp.ticker
    val = report.valuability

    out = [
        f"# {title}: Intrinsic Value Report",
        "",
        f"**Valuability: {val.level}.** {val.rationale}",
        "",
        "### Layer 0 · Verdict",
        "",
        f"> {_verdict_sentence(report)}",
        "",
        "### Layer 1 · Triangulation (independent methods)",
        "",
        _triangulation_table(report),
        "",
        "### Layer 2 · Derivation",
        "",
        _derivation_block(report),
        "",
        "### Layer 3 · Assumptions (the few judgement calls, adjustable)",
        "",
        _assumptions_block(report),
        "",
        "### Layer 4 · Market mirror",
        "",
        _market_mirror_block(report),
        "",
        "### Provenance ledger",
        "",
        _ledger_block(report),
        "",
        "### Data tiers",
        "",
        _TIER_LEGEND,
        "",
        "---",
        "_Assay is not investment advice. It reports a reasoned valuation and its provenance._",
    ]
    return "\n".join(out)
