from __future__ import annotations

from pathlib import Path

ALLOWED_OUTPUT_ROOTS: tuple[str, ...] = (
    "src/ppi/generated",
    "contracts",
    "docs/generated",
    "vscode-extension/src/generated",
)


def assert_within_allowed(relative_path: str) -> None:
    if not any(relative_path.startswith(root) for root in ALLOWED_OUTPUT_ROOTS):
        msg = f"output path '{relative_path}' is not within allowed roots: {ALLOWED_OUTPUT_ROOTS}"
        raise ValueError(msg)
