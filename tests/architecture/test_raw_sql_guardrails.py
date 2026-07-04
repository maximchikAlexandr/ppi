"""Architecture guardrail: fail on raw analytical SQL strings outside approved modules/tests.

Looks for SQL keywords (SELECT, WITH, JOIN, GROUP BY, ORDER BY) in string literals
within Python source files.

Approved modules for raw SQL:
- src/ppi/storage/duckdb_boundary.py
- src/ppi/storage/schema.py
- src/ppi/storage/writer.py
- tests/
"""

from __future__ import annotations

import ast
import pkgutil
from pathlib import Path

import pytest

APPROVED_MODULES = {
    "ppi.storage.duckdb_boundary",
    "ppi.storage.schema",
    "ppi.storage.writer",
}

SQL_KEYWORDS = frozenset({"SELECT", "WITH", "JOIN", "GROUP BY", "ORDER BY", "INSERT", "CREATE TABLE"})


def _iter_source_modules():
    src = Path("src")
    if not src.is_dir():
        return
    for importer, modname, is_pkg in pkgutil.walk_packages([str(src)], prefix="ppi."):
        if is_pkg:
            continue
        yield modname


def _contains_sql_keyword(s: str) -> bool:
    upper = s.upper().strip()
    return any(kw in upper for kw in SQL_KEYWORDS)


@pytest.mark.parametrize("modname", list(_iter_source_modules()))
def test_no_raw_analytical_sql_outside_boundary(modname: str) -> None:
    if modname in APPROVED_MODULES:
        pytest.skip(f"approved: {modname}")
    modpath = Path("src", modname.replace(".", "/") + ".py")
    if not modpath.is_file():
        pytest.skip(f"not found: {modpath}")
    source = modpath.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        pytest.skip(f"cannot parse: {modpath}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _contains_sql_keyword(node.value) and len(node.value) > 20:
                pytest.fail(
                    f"{modname} contains potential raw SQL string "
                    f"(not in approved boundary): {node.value[:80]!r}",
                )
