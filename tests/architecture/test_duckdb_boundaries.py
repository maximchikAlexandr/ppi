"""Architecture guardrail: fail on direct DuckDB imports outside approved modules.

Approved modules for direct duckdb imports:
- src/ppi/storage/duckdb_boundary.py
- src/ppi/storage/schema.py
- src/ppi/storage/writer.py (legacy compatibility)
- tests/ (test files)
- conftest.py, fixtures/
"""

from __future__ import annotations

import ast
import pkgutil
from pathlib import Path

import pytest

APPROVED_MODULES = {
    "ppi.storage.schema",
    "ppi.storage.writer",
}

EXCLUDED_DIRS = {"tests", "scripts", "docs", "frontend", "vscode-extension"}


def _iter_python_modules():
    src = Path("src")
    if not src.is_dir():
        return
    for importer, modname, is_pkg in pkgutil.walk_packages(
        [str(src)], prefix="ppi.",
    ):
        if is_pkg:
            continue
        yield modname


def _module_path(modname: str) -> Path:
    return Path("src", modname.replace(".", "/") + ".py")


@pytest.mark.parametrize("modname", list(_iter_python_modules()))
def test_no_direct_duckdb_import_outside_boundary(modname: str) -> None:
    if modname in APPROVED_MODULES:
        pytest.skip(f"approved: {modname}")
    modpath = _module_path(modname)
    if not modpath.is_file():
        pytest.skip(f"not found: {modpath}")
    source = modpath.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        pytest.skip(f"cannot parse: {modpath}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "duckdb" or alias.name.startswith("duckdb."):
                    pytest.fail(f"{modname} imports duckdb (not in approved boundary)")
        if isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "duckdb" or node.module.startswith("duckdb.")):
                pytest.fail(f"{modname} imports from duckdb (not in approved boundary)")
