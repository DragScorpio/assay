"""Console launcher: ``assay-ui`` starts the Streamlit app.

It also skips Streamlit's first-run email prompt and turns off Streamlit's usage telemetry, so the
app launches clean and asks for nothing. Assay's whole point is no signup and no friction.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _skip_streamlit_email_prompt() -> None:
    """On first run Streamlit asks for an email. Pre-write an empty credentials file (the same
    effect as pressing Enter) so it does not. Never overwrites an existing file."""
    credentials = Path.home() / ".streamlit" / "credentials.toml"
    if not credentials.exists():
        credentials.parent.mkdir(parents=True, exist_ok=True)
        credentials.write_text('[general]\nemail = ""\n', encoding="utf-8")


def main() -> int:
    _skip_streamlit_email_prompt()
    app = str(Path(__file__).resolve().parent / "app.py")
    return subprocess.call(
        [sys.executable, "-m", "streamlit", "run", app, "--browser.gatherUsageStats=false"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
