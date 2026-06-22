# Assay: Design

This is the durable design record. It captures *why* Assay is shaped the way it is, so any future session (or any other person reading the repo) can pick it up without re-deriving the decisions.

## Purpose

Assay exists for two reasons, in this order:

1. **A tool the owner actually uses** to evaluate the worth of US-listed companies (and later commodities) from first principles, not from the day's narrative.
2. A secondary, public artifact: it travels on GitHub and shows the owner can build a real, opinionated tool with AI assistance.

It is **not** an AI-engineering portfolio piece, so it carries no benchmark/eval apparatus to prove model quality. It does keep one rule from good engineering, because trust in the output is the whole product: **the prose may never state a number the math did not produce.**

It is **not investment advice.** It outputs a reasoned valuation and its provenance. Interpreting the gap between value and price is the user's job.

## The core idea

Benjamin Graham's metaphor: in the short run the market is a voting machine, in the long run a weighing machine. The crowd chases the vote. Assay measures the weight: **intrinsic value**, what a business is worth based on the cash it can produce and the assets it controls, independent of today's price.

Intrinsic value is not one magic number. It is a **framework plus primary data plus explicit assumptions**. The equations are durable; the inputs are not. So Assay never reports a point estimate as truth. It reports a *defensible range under stated assumptions, traceable to primary sources*, and it tells you which single assumption moves the answer most.

A hard boundary, stated out loud: Assay tells you *what* a thing is worth, not *when* the market will agree. Those are different questions, and Assay only answers the first.

## Decision 1: Data credibility is tiered, and the tier travels with the number

Assay does not claim data is "true." It ranks data by how hard it is to lie about, stamps every number with that tier and its source, and never lets a low tier silently contaminate a high one.

- **Tier 0, Market fact.** Traded prices, shares outstanding, dividends paid. Nobody fakes a printed trade. Not *value*, but true statements about what the market is doing.
- **Tier 1, Audited disclosure.** SEC filings (10-K, 10-Q via EDGAR) and regulator macro data (FRED). Signed under legal liability, auditor-attested. Not perfect (accounting judgment, rare fraud), but legally and reputationally bonded. Within filings, the **cash-flow statement is the most fraud-resistant** (cash that moved is harder to fake than accrual earnings), which is why owner-earnings leans on it.
- **Tier 2, Derived / opinion.** Multiples, analyst estimates and price targets. Opinion is baked in. Used only as a labeled cross-check, never as an input to the value.
- **Tier 3, Noise.** News tone, pundits, social. Excluded from value; at most a labeled "mood" overlay, never a value input.

In code this is `provenance.Tier` and `provenance.Figure` (a value that knows its `Source` and tier). The engine passes `Figure`s, never bare floats.

## Decision 2: Valuation methods are isolated modules; the engine triangulates

Each method (discounted cash flow, earnings power, asset reproduction value) implements one contract (`models.base.ValuationModel`): tier-tagged figures plus explicit assumptions in, a `ModelResult` (value range plus assumptions used plus figures consumed) out. Methods never read each other's state.

Two payoffs:
- **No interference.** Sandboxed methods can be run, compared, added, or removed independently.
- **Triangulation as truth-seeking.** Three *independent* methods landing on a similar number is a far stronger claim than any single one. Where they diverge is itself worth reading. Convergence of independent methods is the most honest definition of "truth" this tool can offer.

A method may **decline to value** (return a `ModelResult` with `value=None` and a reason). That is a feature (see Decision 4).

## Decision 3: The output is layered (progressive disclosure)

Nobody reads a 40-page report; nobody should trust a one-line hot take either. Assay resolves this with layers, where the summary is a faithful compression of the reasoning beneath it, drillable to the source:

- **Layer 0 (Verdict):** one honest sentence (range, base, price, the decisive assumption).
- **Layer 1 (Triangulation):** the independent methods vs price.
- **Layer 2 (Derivation):** the math and the source of each input.
- **Layer 3 (Assumptions):** the few forward-looking guesses, each overridable, with a sensitivity table and Conservative / Base / Optimistic stances.
- **Layer 4 (Market mirror):** analyst targets, Tier 2, computed *after* and never fed into the value.

Plus a **valuability** banner and a **provenance ledger** (every figure, tier, source).

## Decision 4: Honest refusal, on a gradient

"Valuable vs un-valuable" is a spectrum, not a switch. Every report carries a **valuability** label: how much of the value rests on hard data versus narrative.

- A cash-generative industrial with a long filing history becomes HIGH; the methods do their work.
- A pre-revenue AI/quantum/crypto name with no durable cash flow becomes LOW; Assay reports only the asset floor and the cash, states plainly that the rest is narrative, and **does not fabricate an intrinsic value.** It still explains everything it *does* know and where confirmed fact ends.
- A commodity with centuries of price history and a known marginal cost of production (gold, oil) is HIGH on its own terms (cost-of-production floor, cost of carry). Commodities come later, as their own isolated model modules.

## Decision 5: Assumptions, automated baseline and optional override

The user never has to fetch a number. Assay fills every assumption automatically from history (the baseline), and the user can read the whole report without typing anything.

The **override** exists because the future is a guess. The user may change only the few forward-looking `Assumption`s (growth, terminal growth, discount rate), never facts like price or cash flow, which are Tier 0/1 and locked. An override is the user's *opinion*, not a looked-up value (e.g. "I think this industry is slowing, try 2% growth"). For non-experts, **stances** (Conservative / Base / Optimistic) move the assumptions together without typing a number.

This is the philosophy made usable: facts are fixed and sourced; the future is explicit and yours to challenge.

## Decision 6: Math in code, the LLM only narrates, and a guard enforces it

Every number comes from deterministic code over sourced data. The full report renders with **no LLM and no API key**. An LLM (behind a provider-agnostic interface, `narrate.llm`) is an *optional* layer that writes the plain-English prose around the numbers: the business description, the interpretation of the gap, the plain-language meaning of each term.

The moment an LLM "estimates" a cash flow, the whole trust premise is gone. So a deterministic guard (`narrate.assert_grounded`) checks the generated prose: every number it mentions must already exist in the computed report. Prose that introduces a new number is rejected. This is the one discipline kept from rigorous AI work, and it is here for the user's own trust, not for a scoreboard.

## Decision 7: Jargon, plain word out front and exact term attached

Finance terms are the durable vocabulary and are not thrown away, but they never lead. The default label is plain ("yearly cash profit"); the exact term ("free cash flow") rides alongside; the one-line definition sits behind an expandable glossary. Friendly on the surface, precise underneath, and it quietly teaches the real vocabulary over time.

## Data sources (US-listed companies first)

| Tier | Source | How | Note |
|---|---|---|---|
| 0 | Prices | Polygon.io / Tiingo / Alpaca | reputable APIs agree to the cent; pick one |
| 1 | Filings | **SEC EDGAR** `data.sec.gov` XBRL company-facts JSON | free, structured, authoritative, straight from the regulator |
| 1 | Macro / rates | **FRED** (St. Louis Fed) API | risk-free rate for the discount rate |
| 2 | Analyst targets | Financial Modeling Prep / Finnhub | opinion; comparison only |

EDGAR plus FRED plus one price API is the honest backbone, mostly free and regulator-sourced. `yfinance` is fine for a throwaway prototype but is scraped and unofficial, so it is not the production spine of a truth tool. Commodities later use the same government-primary pattern: EIA (energy), USGS (metals), FRED / World Bank (long price history).

## Architecture

```
assay/
  provenance.py        Tier + Source + Figure  (the backbone type)
  data/                per-source adapters, each returns tier-tagged Figures
    sample.py          a fictional company so `assay demo` runs with no network
    edgar.py           SEC EDGAR (Tier 1)   [skeleton: endpoint documented]
    fred.py            FRED macro (Tier 1)  [stub]
    prices.py          price quote (Tier 0) [stub]
    analysts.py        analyst targets (Tier 2, comparison only) [stub]
  models/              isolated valuation methods
    base.py            ValuationModel contract + Assumption / ValueRange / ModelResult / CompanyInputs
    dcf.py             discounted cash flow (two-stage)  [implemented]
    earnings_power.py  earnings power value              [stub]
    asset_value.py     asset reproduction value          [stub]
  engine/
    triangulate.py     run all methods, summarize convergence
    valuability.py     score how anchorable the company is
    report.py          assemble + render the layered report (deterministic)
  narrate/
    llm.py             provider-agnostic LLM (anthropic | openai | offline)
    narrate.py         optional prose + assert_grounded guard
  cli.py               `assay demo`, `assay <TICKER>`
```

## Non-goals

- Not investment advice; no buy/sell/target output.
- No portfolio tracking, no position sizing, no brokerage integration.
- No sentiment/technical signals as value inputs (Tier 3 stays out).
- No AI-computed numbers, ever.

## Roadmap

- **v0.1 (now):** scaffold plus deterministic spine; `assay demo` renders the full layered report on the sample company; DCF implemented; provenance plus grounding guard unit-tested.
- **v0.2:** real SEC EDGAR adapter (company-facts XBRL into `CompanyInputs`), FRED risk-free rate, one price provider; `assay <TICKER>` works on a real company.
- **v0.3:** earnings-power and asset-reproduction methods (real triangulation); valuability gradient tuned; analyst market-mirror via FMP/Finnhub.
- **later:** commodities as their own model modules (gold, oil); optional richer LLM narration; a simple local web view of the report.
