"""Python complexity analysis pipeline stage.

Converts the imperative complexity analysis flow into typed stage
contracts. Complexity distribution/stat reducers are extracted as
pure functions.
"""

from __future__ import annotations

from ppi.core.odoo.pipeline import (
    AnalysisArtifacts,
    analyze_python_complexity,
)
from ppi.rop.types import StageResult


def python_complexity_analysis_pipeline(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, None]:
    """Spec-named pipeline: analyze Python complexity."""
    return python_complexity_analysis_stage(artifacts)


def python_complexity_analysis_stage(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, None]:
    """Analyze Python complexity for all modules."""
    updated = analyze_python_complexity(artifacts.modules)
    return Ok(artifacts.replace(modules=updated))
