"""The grounding guard and a deterministic plain-English summary.

``assert_grounded`` is the one rule Assay keeps from rigorous AI work, and it is here for the user's
own trust: prose may only restate numbers the math already produced. It scans for *financial*
magnitudes (anything with a ``$`` or ``%``, a comma or decimal, or magnitude ≥ 100, excluding
year-like integers) and flags any that are not in the report's set of allowed numbers.
"""

from __future__ import annotations

import re

from ..engine.report import Report, fmt_share

_NUM_TOKEN = re.compile(r"(\$)?(\d[\d,]*(?:\.\d+)?)(%)?")


def _financial_numbers(text: str) -> list[float]:
    """Pull financial-looking magnitudes out of prose (skip plain small integers and years)."""
    out: list[float] = []
    for m in _NUM_TOKEN.finditer(text):
        dollar, num, pct = m.group(1), m.group(2), m.group(3)
        try:
            val = float(num.replace(",", ""))
        except ValueError:
            continue
        has_decimal = "." in num or "," in num
        looks_financial = bool(dollar) or bool(pct) or has_decimal or val >= 100
        is_year = not dollar and not pct and not has_decimal and 1900 <= val <= 2100
        if looks_financial and not is_year:
            out.append(round(val, 2))
    return out


def assert_grounded(prose: str, allowed: set[float], tol: float = 0.5) -> list[float]:
    """Return the financial numbers in ``prose`` that are NOT in ``allowed`` (empty == grounded)."""
    allowed_r = {round(a, 2) for a in allowed}
    ungrounded: list[float] = []
    for v in _financial_numbers(prose):
        if not any(abs(v - a) <= tol for a in allowed_r):
            ungrounded.append(v)
    return ungrounded


def plain_summary(report: Report) -> str:
    """A short, deterministic, grounded summary built only from report numbers (no LLM).

    By construction every number it states is in ``report.allowed``, so it passes the guard. This is
    the offline narration; an LLM, when enabled, would produce richer prose checked the same way.
    """
    r = report.primary
    if r is None or r.value is None:
        return (
            f"Assay declined to value {report.inputs.name or report.inputs.ticker} on fundamentals "
            f"(valuability {report.valuability.level})."
        )
    price = report.inputs.price
    price_clause = f" against a market price of {fmt_share(price.value)}" if price else ""
    return (
        f"{report.inputs.name or report.inputs.ticker}: intrinsic value "
        f"{fmt_share(r.value.low)} to {fmt_share(r.value.high)} per share, base "
        f"{fmt_share(r.value.base)}{price_clause}. Valuability {report.valuability.level}."
    )
