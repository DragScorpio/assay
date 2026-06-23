"""Console launcher: ``assay-ui`` starts the Streamlit app."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    app = str(Path(__file__).resolve().parent / "app.py")
    return subprocess.call([sys.executable, "-m", "streamlit", "run", app])


if __name__ == "__main__":
    raise SystemExit(main())
