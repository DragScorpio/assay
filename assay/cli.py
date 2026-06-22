"""Command line entry point.

assay demo            full report on a fictional company, no keys needed
assay value TICKER    value a real US-listed company (needs data keys; lands in v0.2)
assay TICKER          shorthand for `assay value TICKER`
"""

from __future__ import annotations

import sys
from typing import Optional

from .data.analysts import fetch_targets
from .data.sample import acme_inputs
from .engine.report import build_report, render_markdown
from .engine.triangulate import triangulate
from .engine.valuability import assess
from .models import DEFAULT_MODELS
from .models.base import CompanyInputs

_USAGE = "usage: assay <demo | value TICKER | TICKER>"


def _report_for(inputs: CompanyInputs) -> str:
    triangulation = triangulate(inputs, DEFAULT_MODELS)
    valuability = assess(inputs)
    analyst = fetch_targets(inputs.ticker)
    report = build_report(inputs, triangulation, valuability, analyst)
    return render_markdown(report)


def main(argv: Optional[list[str]] = None) -> int:
    # The report is plain Markdown; force UTF-8 so it prints on Windows consoles (cp1252) too.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(_USAGE)
        return 0

    cmd = argv[0]
    if cmd == "demo":
        print(_report_for(acme_inputs()))
        return 0

    ticker = argv[1] if cmd == "value" and len(argv) > 1 else cmd

    import httpx

    from .data.edgar import fetch_company_inputs

    try:
        inputs = fetch_company_inputs(ticker)
    except (LookupError, NotImplementedError) as exc:
        print(f"assay: {exc}", file=sys.stderr)
        return 2
    except httpx.HTTPError as exc:
        print(f"assay: could not reach SEC EDGAR ({exc})", file=sys.stderr)
        return 2
    print(_report_for(inputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
