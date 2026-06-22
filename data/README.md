# data/

Local working directory for Assay. Everything here except this file is gitignored.

- `cache/`: cached API responses and downloaded SEC filings. Assay fetches these on demand; they are never committed (they are large and reproducible).
- `.llm_cache/`: cached LLM responses for the optional narrator, so re-runs are free and deterministic.

Primary data comes straight from the source at run time:

- **SEC EDGAR** (`data.sec.gov`): audited filings (Tier 1). Requires a descriptive `ASSAY_SEC_USER_AGENT`.
- **FRED** (St. Louis Fed): macro / risk-free rate (Tier 1). Requires `FRED_API_KEY`.
- **A price provider**: Polygon / Tiingo / Alpaca (Tier 0).

See [`../.env.example`](../.env.example) for configuration.
