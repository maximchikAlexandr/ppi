"""Python AST facts pipeline stage.

Extracts AST file read/parse into an adapter, keeping the
``ast.NodeVisitor`` shell internal while exposing a function-shaped
AST facts stage.
"""

from __future__ import annotations

from pathlib import Path

from expression.core.result import Error, Ok

from ppi.core.odoo.pipeline import (
    AnalysisArtifacts,
    analyze_python_modules,
)
from ppi.rop.errors import RecoverableDomainFailure
from ppi.rop.types import StageResult


def python_ast_facts_pipeline(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, RecoverableDomainFailure]:
    """Spec-named pipeline: extract AST facts."""
    return python_ast_facts_stage(artifacts)


def python_ast_facts_stage(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, RecoverableDomainFailure]:
    """Run Python AST facts extraction across all modules.

    The AST visitor shell remains internal to this stage; only
    function-shaped facts are returned.
    """
    try:
        updated = analyze_python_modules(artifacts.modules)
        return Ok(artifacts.replace(modules=updated))
    except Exception as exc:
        return Error(
            RecoverableDomainFailure(
                stage="python_ast_facts",
                message=str(exc),
                safe_input_id="",
                cause=exc,
            )
        )
