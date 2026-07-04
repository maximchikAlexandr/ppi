"""Provider map attachment pipeline stage.

Builds owner/provider indexes (model_owners, field_providers,
method_providers) from analyzed modules.
"""

from __future__ import annotations

from ppi.core.odoo.pipeline import (
    AnalysisArtifacts,
    attach_provider_maps,
)


def provider_index_pipeline(
    artifacts: AnalysisArtifacts,
) -> AnalysisArtifacts:
    """Spec-named pipeline: build provider indexes."""
    return provider_index_stage(artifacts)


def provider_index_stage(
    artifacts: AnalysisArtifacts,
) -> AnalysisArtifacts:
    """Attach provider maps to analysis artifacts (pure, infallible)."""
    return attach_provider_maps(artifacts)
