"""Module enrichment pipeline composition.

Composes metrics, complexity, AST facts, and model expression
resolution into the top-level ``module_enrichment_pipeline``.
"""

from __future__ import annotations

from expression.core.result import Error, Ok

from ppi.core.odoo.pipeline import AnalysisArtifacts
from ppi.rop.types import StageResult


def module_enrichment_pipeline(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, str]:
    """Run the full module enrichment pipeline.

    Composes:
      1. Module code metrics
      2. Python complexity analysis
      3. Python AST facts
    """
    from ppi.core.pipelines.module_code_metrics import module_code_metrics_stage
    from ppi.core.pipelines.python_ast_facts import python_ast_facts_stage
    from ppi.core.pipelines.python_complexity import python_complexity_analysis_stage

    result = module_code_metrics_stage(artifacts)
    if result.is_error():
        return Error("Module code metrics failed")

    enriched = result.default_value(None)
    result = python_complexity_analysis_stage(enriched)
    if result.is_error():
        return Error("Complexity analysis failed")

    enriched = result.default_value(None)
    result = python_ast_facts_stage(enriched)
    if result.is_error():
        return Error("AST facts failed")

    return Ok(result.default_value(None))
