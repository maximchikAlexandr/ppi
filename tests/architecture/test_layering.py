"""Architecture guardrail: check migrated core/query modules do not import CLI/server adapters."""

from __future__ import annotations

import ast
import pkgutil
from pathlib import Path

import pytest

FORBIDDEN_IMPORTS_IN_CORE = {
    "ppi.cli",
    "ppi.server",
    "ppi.adapters",
}

CORE_PREFIXES = {
    "ppi.core",
    "ppi.history.stages_",
    "ppi.query",
    "ppi.storage.ibis_",
}

EXCLUDED_DIRS = {"tests", "scripts", "docs"}


def _iter_core_modules():
    src = Path("src")
    if not src.is_dir():
        return
    for importer, modname, is_pkg in pkgutil.walk_packages([str(src)], prefix="ppi."):
        if is_pkg:
            continue
        if any(modname.startswith(p) for p in CORE_PREFIXES):
            yield modname


@pytest.mark.parametrize("modname", list(_iter_core_modules()))
def test_core_modules_do_not_import_adapters(modname: str) -> None:
    modpath = Path("src", modname.replace(".", "/") + ".py")
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
                if any(alias.name.startswith(f) for f in FORBIDDEN_IMPORTS_IN_CORE):
                    pytest.fail(f"{modname} imports {alias.name} (forbidden in core)")
        if isinstance(node, ast.ImportFrom):
            if node.module:
                if any(node.module.startswith(f) for f in FORBIDDEN_IMPORTS_IN_CORE):
                    pytest.fail(f"{modname} imports from {node.module} (forbidden in core)")
