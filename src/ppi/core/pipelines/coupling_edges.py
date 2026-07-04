"""Coupling edge attachment and scoring pipeline stages.

Stages:
  - ``attach_edges_and_scores_stage``: build cross-module edges and scores.
  - ``compute_module_scores_stage``: compute per-module scores from edges.
"""

from __future__ import annotations

from ppi.core.odoo.pipeline import (
    AnalysisArtifacts,
    attach_edges_and_scores,
)
from ppi.rop.types import StageResult


def coupling_edge_detection_pipeline(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, None]:
    """Spec-named pipeline: detect coupling edges."""
    return attach_edges_and_scores_stage(artifacts)


def attach_edges_and_scores_stage(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, None]:
    """Build cross-module edges and score aggregates."""
    return Ok(attach_edges_and_scores(artifacts))
