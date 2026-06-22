"""SEC EDGAR adapter (Tier 1) for audited filings straight from the U.S. regulator.

EDGAR is the crown jewel: free, structured, legally bonded. Two endpoints:

  ticker -> CIK   https://www.sec.gov/files/company_tickers.json
  facts           https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json

The company-facts JSON holds every XBRL-tagged value the filer reported, grouped by namespace
(`us-gaap`, `dei`) and concept, each with a list of period observations. The real work is *picking*
the right observation: the latest annual figure for flow concepts (cash flow, revenue) and the
latest reported balance for instant concepts (shares, cash, debt). US-GAAP tags vary across filers,
so each field tries a few candidate concepts.

Fair-access rules require a descriptive ``User-Agent`` with contact info (``ASSAY_SEC_USER_AGENT``)
and a request rate at or below 10/second. The network fetch and the parsing are kept separate so the
normalization can be unit-tested against a fixture with no network.
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any, Callable, Optional

import httpx

from ..models.base import CompanyInputs
from ..provenance import Figure, Source, Tier

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

#: Forms that report a full fiscal year. startswith() so amendments (10-K/A) count too.
_ANNUAL_FORM_PREFIXES = ("10-K", "20-F", "40-F")


def user_agent() -> str:
    """The descriptive User-Agent EDGAR's fair-access policy requires."""
    return os.environ.get("ASSAY_SEC_USER_AGENT", "assay/0.1 (set ASSAY_SEC_USER_AGENT)")


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": user_agent(), "Accept-Encoding": "gzip, deflate"},
        timeout=30.0,
    )


# --------------------------------------------------------------------------- network


def ticker_to_cik(ticker: str, client: httpx.Client) -> int:
    """Map a ticker to its SEC CIK via the official ticker list."""
    data = client.get(COMPANY_TICKERS_URL).json()
    wanted = ticker.upper()
    for row in data.values():
        if str(row.get("ticker", "")).upper() == wanted:
            return int(row["cik_str"])
    raise LookupError(f"ticker {ticker!r} not found in SEC company list")


def fetch_company_facts(cik: int, client: httpx.Client) -> dict[str, Any]:
    """Fetch the raw XBRL company-facts JSON for a CIK."""
    resp = client.get(COMPANY_FACTS_URL.format(cik=cik))
    resp.raise_for_status()
    return resp.json()


def fetch_company_inputs(ticker: str, client: Optional[httpx.Client] = None) -> CompanyInputs:
    """Build :class:`CompanyInputs` for a ticker from live EDGAR data.

    Price is left as ``None`` here: it is a Tier 0 market fact and comes from the price adapter,
    not from filings.
    """
    owns = client is None
    client = client or _client()
    try:
        cik = ticker_to_cik(ticker, client)
        facts = fetch_company_facts(cik, client)
    finally:
        if owns:
            client.close()
    return parse_company_facts(facts, cik, ticker.upper())


# --------------------------------------------------------------------------- pickers


def _is_annual(entry: dict) -> bool:
    return str(entry.get("form", "")).startswith(_ANNUAL_FORM_PREFIXES)


def _pick_annual(entries: list[dict]) -> Optional[dict]:
    """Latest full-year observation of a flow concept (revenue, cash flow)."""
    best: Optional[dict] = None
    for e in entries:
        if not _is_annual(e):
            continue
        start, end = e.get("start"), e.get("end")
        if not start or not end:
            continue
        try:
            days = (date.fromisoformat(end) - date.fromisoformat(start)).days
        except ValueError:
            continue
        if not 330 <= days <= 400:  # a fiscal year, not a quarter
            continue
        if best is None or end > best["end"]:
            best = e
    return best


def _pick_instant(entries: list[dict]) -> Optional[dict]:
    """Latest reported balance of an instant concept (shares, cash, debt)."""
    best: Optional[dict] = None
    for e in entries:
        end = e.get("end")
        if not end:
            continue
        if best is None or (end, e.get("filed", "")) > (best["end"], best.get("filed", "")):
            best = e
    return best


def _concept(
    facts: dict,
    candidates: list[tuple[str, str]],
    units: list[str],
    picker: Callable[[list[dict]], Optional[dict]],
) -> Optional[tuple[dict, str]]:
    """The freshest (chosen observation, concept name) across candidate tags.

    Filers switch XBRL tags over time (e.g. Apple moved off ``Revenues`` years ago), so an older tag
    can still hold stale data. Rather than take the first tag that has any value, gather each tag's
    chosen observation and keep the one with the latest period end. That way a tag the company
    abandoned never wins over the one it currently files.
    """
    root = facts.get("facts", {})
    found: list[tuple[dict, str]] = []
    for namespace, concept in candidates:
        node = root.get(namespace, {}).get(concept)
        if not node:
            continue
        for unit in units:
            entries = node.get("units", {}).get(unit)
            if not entries:
                continue
            chosen = picker(entries)
            if chosen is not None:
                found.append((chosen, concept))
                break  # this tag's best in its first available unit
    if not found:
        return None
    return max(found, key=lambda c: (c[0].get("end", ""), c[0].get("filed", "")))


def _source(cik: int, chosen: dict, detail: str) -> Source:
    accn = chosen.get("accn", "")
    return Source(
        name=f"SEC EDGAR {chosen.get('form', 'filing')}",
        tier=Tier.FILING,
        locator=f"CIK{cik:010d} {detail} accn {accn}".strip(),
        as_of=chosen.get("end", ""),
    )


def _fy_label(stub: str, chosen: dict) -> str:
    fy = chosen.get("fy")
    return f"{stub} (FY{fy})" if fy else f"{stub} (annual)"


# --------------------------------------------------------------------------- parsing


def parse_company_facts(facts: dict, cik: int, ticker: str = "") -> CompanyInputs:
    """Normalize raw company-facts JSON into tier-1 Figures. Pure, no network, so it is testable.

    Anything Assay cannot find is left ``None`` rather than guessed, so the report degrades honestly.
    """
    name = facts.get("entityName", "")

    shares = _concept(
        facts,
        [
            ("dei", "EntityCommonStockSharesOutstanding"),
            ("us-gaap", "CommonStockSharesOutstanding"),
        ],
        ["shares"],
        _pick_instant,
    )
    shares_fig = (
        Figure(
            float(shares[0]["val"]),
            "shares",
            _source(cik, shares[0], shares[1]),
            "Shares outstanding",
        )
        if shares
        else None
    )

    # Free cash flow = operating cash flow minus capital expenditure, latest annual.
    ocf = _concept(
        facts,
        [
            ("us-gaap", "NetCashProvidedByUsedInOperatingActivities"),
            ("us-gaap", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"),
        ],
        ["USD"],
        _pick_annual,
    )
    capex = _concept(
        facts,
        [
            ("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),
            ("us-gaap", "PaymentsToAcquireProductiveAssets"),
        ],
        ["USD"],
        _pick_annual,
    )
    fcf_fig = None
    if ocf and capex:
        chosen = ocf[0]
        fcf_val = float(chosen["val"]) - float(capex[0]["val"])
        fcf_fig = Figure(
            fcf_val,
            "USD",
            _source(cik, chosen, "OperatingCashFlow-CapEx"),
            _fy_label("Free cash flow", chosen),
        )

    # Net debt = total debt minus cash, latest reported balance.
    cash = _concept(
        facts, [("us-gaap", "CashAndCashEquivalentsAtCarryingValue")], ["USD"], _pick_instant
    )
    debt = _concept(
        facts,
        [("us-gaap", "LongTermDebt"), ("us-gaap", "LongTermDebtNoncurrent")],
        ["USD"],
        _pick_instant,
    )
    net_debt_fig = None
    if cash and debt:
        nd = float(debt[0]["val"]) - float(cash[0]["val"])
        net_debt_fig = Figure(nd, "USD", _source(cik, debt[0], "LongTermDebt-Cash"), "Net debt")

    revenue = _concept(
        facts,
        [
            ("us-gaap", "Revenues"),
            ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
            ("us-gaap", "SalesRevenueNet"),
        ],
        ["USD"],
        _pick_annual,
    )
    revenue_fig = (
        Figure(
            float(revenue[0]["val"]),
            "USD",
            _source(cik, revenue[0], revenue[1]),
            _fy_label("Revenue", revenue[0]),
        )
        if revenue
        else None
    )

    return CompanyInputs(
        ticker=ticker,
        name=name,
        price=None,  # Tier 0, filled by the price adapter (next in v0.2)
        shares_outstanding=shares_fig,
        free_cash_flow_ttm=fcf_fig,
        net_debt=net_debt_fig,
        revenue_ttm=revenue_fig,
    )
