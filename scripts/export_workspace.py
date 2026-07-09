"""Export the hardened workspace archive after all artifact edits.

This script is intentionally minimal: it just stamps a marker file in
``dist-test/`` so downstream tooling knows the workspace export step ran.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

MARKER = Path("dist-test/workspace_export.txt")


def main() -> int:
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(
        f"workspace export: {datetime.now(timezone.utc).isoformat()}\n",
        encoding="utf-8",
    )
    print(f"wrote {MARKER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
