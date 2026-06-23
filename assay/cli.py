"""Command line entry point.

assay demo            full report on a fictional company, no keys needed
assay value TICKER    value a real US-listed company
assay TICKER          shorthand for `assay value TICKER`
"""

from __future__ import annotations

import sys
from typing import Optional

from .data.sample import acme_inputs
from .engine.report import render_markdown
from .pipeline import load_inputs, report_for

_USAGE = "usage: assay <demo | value TICKER | TICKER>"


def main(argv: Optional[list[str]] = None) -> int:
    # Load a local .env (gitignored) so the SEC User-Agent and any keys work without shell exports.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
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
        print(render_markdown(report_for(acme_inputs())))
        return 0

    ticker = argv[1] if cmd == "value" and len(argv) > 1 else cmd

    import httpx

    try:
        inputs = load_inputs(ticker)
    except (LookupError, NotImplementedError) as exc:
        print(f"assay: {exc}", file=sys.stderr)
        return 2
    except httpx.HTTPError as exc:
        print(f"assay: could not reach SEC EDGAR ({exc})", file=sys.stderr)
        return 2

    print(render_markdown(report_for(inputs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
