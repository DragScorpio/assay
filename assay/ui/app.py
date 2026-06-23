"""Assay UI: a local Streamlit app over the valuation engine.

Run it with:  assay-ui   (or: streamlit run assay/ui/app.py)

The app reuses the same deterministic engine as the CLI (:mod:`assay.pipeline`). The sidebar sliders
override the three forward-looking assumptions and the whole report recomputes live; the facts never
change.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from assay.engine.report import fmt_pct, fmt_share, render_markdown
from assay.pipeline import load_inputs, report_for

st.set_page_config(page_title="Assay", layout="centered")
st.title("Assay")
st.caption(
    "What a US-listed company is worth, from primary-source filings. Three methods, the live "
    "market price, every number sourced. Not investment advice."
)

ticker = st.text_input("US-listed ticker", value="AAPL").strip().upper()
if not ticker:
    st.stop()

try:
    inputs = load_inputs(ticker)
except Exception as exc:  # unknown ticker, or a data source is down
    st.error(f"Could not load {ticker}: {exc}")
    st.stop()

# A first pass with no overrides gives the data-derived assumption defaults for the sliders.
base = report_for(inputs)
defaults = {a.key: a.value for a in (base.primary.assumptions if base.primary else [])}

overrides: dict[str, float] = {}
if base.primary is not None:
    st.sidebar.header("Assumptions")
    st.sidebar.caption(
        "Facts are locked. Drag a slider to override a guess; leave it to keep the sourced value."
    )
    # An untouched slider is NOT treated as an override, so it keeps the sourced value and its real
    # basis (revenue CAGR, live Treasury) rather than reading "your override". This also makes an
    # untouched UI match the CLI exactly, since the model uses the same data values.
    g0 = round(defaults.get("growth_10y", 0.04) * 100, 2)
    t0 = round(defaults.get("terminal_growth", 0.025) * 100, 2)
    w0 = round(defaults.get("wacc", 0.09) * 100, 2)
    growth = st.sidebar.slider("Yearly growth, 10y (%)", -5.0, 25.0, g0, 0.1)
    terminal = st.sidebar.slider("Forever-growth (%)", 0.0, 4.0, t0, 0.1)
    wacc = st.sidebar.slider("Discount rate (%)", 3.0, 20.0, w0, 0.1)
    if growth != g0:
        overrides["growth_10y"] = growth / 100
    if terminal != t0:
        overrides["terminal_growth"] = terminal / 100
    if wacc != w0:
        overrides["wacc"] = wacc / 100

report = report_for(inputs, overrides or None)

# --- headline: the range leads, because that is what people read first ---
st.subheader(report.inputs.name or ticker)
level = report.valuability.level
color = {"HIGH": "green", "MEDIUM": "orange", "LOW": "red"}.get(level, "gray")
st.markdown(f"**Valuability: :{color}[{level}].** {report.valuability.rationale}")

if report.primary is not None and report.primary.value is not None:
    v = report.primary.value
    st.markdown(f"### Intrinsic value: {fmt_share(v.low)} to {fmt_share(v.high)} per share")
    cols = st.columns(2)
    cols[0].metric("Base case", fmt_share(v.base))
    if report.inputs.price is not None:
        delta = (report.inputs.price.value - v.base) / v.base * 100
        cols[1].metric(
            "Market price", fmt_share(report.inputs.price.value), f"{delta:+.0f}% vs base"
        )
    # Show the assumptions actually used, with their source, so any shift in the range is
    # explainable (e.g. a live discount rate vs the default when FRED is briefly unreachable).
    used = {a.key: a for a in report.primary.assumptions}
    bits = []
    if "growth_10y" in used:
        g = used["growth_10y"]
        bits.append(f"growth {fmt_pct(g.value)} ({g.basis})")
    if "wacc" in used:
        w = used["wacc"]
        bits.append(f"discount rate {fmt_pct(w.value)} ({w.basis})")
    if bits:
        st.caption("Driven by: " + "  ·  ".join(bits))
else:
    st.warning("Assay declined to value this company on fundamentals. See the full report below.")
    if report.inputs.price is not None:
        st.metric("Market price", fmt_share(report.inputs.price.value))

# --- triangulation, as a horizontal bar chart so the method labels read normally ---
rows = [
    {"method": r.method, "USD per share": round(r.value.base, 2)}
    for r in report.triangulation.valued
    if r.value is not None
]
if report.inputs.price is not None:
    rows.append({"method": "Market price", "USD per share": round(report.inputs.price.value, 2)})
if rows:
    st.subheader("Triangulation")
    st.bar_chart(
        pd.DataFrame(rows).set_index("method"),
        horizontal=True,
        x_label="USD per share",
    )
    st.caption("Each bar is the per-share value from one method, next to what the market charges.")

# --- the full deterministic report, every layer and source ---
with st.expander("Full report (every layer, every source)"):
    st.markdown(render_markdown(report))
