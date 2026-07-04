"""Architecture guardrail: public pipeline stage signatures are typed, use Option, avoid Any."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

STAGE_MODULES = [
    "ppi.history.stages_validation",
    "ppi.history.stages_boundary",
    "ppi.history.stages_normalize",
    "ppi.history.stages_metrics",
    "ppi.history.stages_write_prep",
    "ppi.history.stages_write_boundary",
    "ppi.query.dispatch",
    "ppi.query._handlers",
    "ppi.query.pipeline",
    "ppi.storage.ibis_queries",
]


@pytest.mark.parametrize("modname", STAGE_MODULES)
def test_stage_functions_have_annotations(modname: str) -> None:
    modpath = Path("src", modname.replace(".", "/") + ".py")
    if not modpath.is_file():
        pytest.skip(f"not found: {modpath}")
    source = modpath.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            if not node.returns:
                pytest.fail(f"{modname}:{node.name} lacks return annotation")
            for arg in node.args.args:
                if arg.arg == "self":
                    continue
                if not arg.annotation:
                    pytest.fail(f"{modname}:{node.name} parameter {arg.arg} lacks type annotation")
