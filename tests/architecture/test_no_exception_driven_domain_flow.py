"""Architecture guardrail: recoverable domain code does not raise/catch broad exceptions for control flow."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PURE_MODULES = [
    "ppi.history.stages_validation",
    "ppi.history.stages_normalize",
    "ppi.history.stages_metrics",
    "ppi.history.stages_write_prep",
]


@pytest.mark.parametrize("modname", PURE_MODULES)
def test_no_broad_except_in_pure_stages(modname: str) -> None:
    modpath = Path("src", modname.replace(".", "/") + ".py")
    if not modpath.is_file():
        pytest.skip(f"not found: {modpath}")
    source = modpath.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "Exception"):
                pytest.fail(f"{modname} has bare/broad except; use specific exception types")
