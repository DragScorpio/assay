"""SEC EDGAR adapter (Tier 1) — audited filings straight from the U.S. regulator.

EDGAR is the crown jewel: free, structured, legally bonded. The company-facts endpoint returns
XBRL-tagged financials as JSON:

    https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json

Fair-access rules require a descriptive ``User-Agent`` with contact info (``ASSAY_SEC_USER_AGENT``)
and a request rate at or below 10/second. A ticker is mapped to a zero-padded 10-digit CIK via
``https://www.sec.gov/files/company_tickers.json``.

Implemented in v0.2. The real work is normalization, not arithmetic: US-GAAP concept names vary
across filers (e.g. free cash flow is operating cash flow minus capex, with several possible tags),
and restatements must be handled. Until then this raises rather than returning a guess.
"""

from __future__ import annotations

import os

from ..models.base import CompanyInputs

COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"


def user_agent() -> str:
    """The descriptive User-Agent EDGAR's fair-access policy requires."""
    return os.environ.get("ASSAY_SEC_USER_AGENT", "assay/0.1 (set ASSAY_SEC_USER_AGENT)")


def fetch_company_inputs(ticker: str) -> CompanyInputs:
    """Build :class:`CompanyInputs` from EDGAR company-facts. Not implemented until v0.2."""
    raise NotImplementedError(
        "EDGAR adapter lands in v0.2. For now use `assay demo` for the fictional company. "
        "See this module's docstring for the company-facts endpoint and the normalization plan."
    )
