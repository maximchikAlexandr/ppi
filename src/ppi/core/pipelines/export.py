"""Freeze/export pipeline stage.

Converts analysis artifacts into the serializable ``AnalysisBatch``
contract for persistence, query, and API delivery.
"""

from __future__ import annotations

from ppi.core.analysis_mappers import artifacts_to_analysis_batch
from ppi.core.contracts import AnalysisBatch, CommitRef
from ppi.core.odoo.pipeline import AnalysisArtifacts


def analysis_freeze_export_pipeline(
    artifacts: AnalysisArtifacts,
    commit: CommitRef,
) -> AnalysisBatch:
    """Spec-named pipeline: freeze artifacts to analysis batch."""
    return freeze_and_export_analysis_batch(artifacts, commit)


def freeze_and_export_analysis_batch(
    artifacts: AnalysisArtifacts,
    commit: CommitRef,
) -> AnalysisBatch:
    """Freeze analysis artifacts into an ``AnalysisBatch`` (pure, infallible)."""
    return artifacts_to_analysis_batch(artifacts, commit)
