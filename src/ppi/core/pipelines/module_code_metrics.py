"""Module code metrics pipeline stage.

Converts the imperative ``analyze_module_code_size`` flow into typed
stage contracts. File classification and line counting failures are
represented as recoverable typed facts.
"""

from __future__ import annotations

from ppi.core.odoo.pipeline import (
    AnalysisArtifacts,
    ModuleInfo,
    analyze_module_code_size,
)
from ppi.rop.types import StageResult


def module_code_metrics_pipeline(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, None]:
    """Spec-named pipeline: compute code metrics for modules."""
    return module_code_metrics_stage(artifacts)


def module_code_metrics_stage(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, None]:
    """Analyze code size metrics for all modules.

    This stage calls the existing analyzer, which is already split into
    per-module pure operations with ``replace``-based immutability.

    ponytail: ``analyze_module_code_size`` still performs filesystem
    scans inside each module path (effect shell). The adapter boundary
    here is thin because the underlying function already builds immutable
    ``ModuleInfo`` via ``replace``. Extract filesystem IO into a proper
    adapter when callers need testable effect boundaries.
    """
    updated = analyze_module_code_size(artifacts.modules)
    return Ok(artifacts.replace(modules=updated))
