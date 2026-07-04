"""Odoo project analysis pipeline — top-level composition.

Composes the full analysis railway from named stages. Every stage
returns ``StageResult`` so the pipeline is a typed composition, not a
top-level pipe wrapper around unchanged imperative code.
"""

from __future__ import annotations

from pathlib import Path

from expression.core import pipe
from expression.core.result import Error, Ok, Result

from ppi.core.contracts import AnalysisBatch, CommitRef
from ppi.core.errors import AnalysisError, PipelineUnexpectedError
from ppi.core.odoo.pipeline import (
    AnalysisArtifacts,
    ReportConfig,
    build_report_config,
    discover_analysis_artifacts,
    enrich_modules_with_code_analysis,
    resolve_addons_paths,
    validate_addons_paths,
)
from ppi.rop.errors import TypedStageError
from ppi.rop.types import StageResult


def report_config_stage(
    project_label: str,
    all_modules: bool = True,
) -> ReportConfig:
    """Build the report configuration for the analysis."""
    return build_report_config(project_label=project_label, all_modules=all_modules)


def resolve_and_validate_addons_stage(
    addons_paths: tuple[Path, ...],
) -> StageResult[tuple[Path, ...], TypedStageError]:
    """Resolve and validate addons paths as a typed ROP stage."""
    resolved = resolve_addons_paths(addons_paths)
    validated = validate_addons_paths(resolved)
    if validated.is_error():
        from ppi.rop.errors import ValidationFailure

        return Error(
            ValidationFailure(
                stage="resolve_and_validate_addons",
                message=str(validated.error),
                safe_input_id=str(addons_paths),
            )
        )
    return Ok(validated.default_value(None))


def discover_artifacts_stage(
    config: ReportConfig,
    addons_paths: tuple[Path, ...],
) -> StageResult[AnalysisArtifacts, TypedStageError]:
    """Discover modules and initialize analysis artifacts."""
    discovered = discover_analysis_artifacts(config, addons_paths)
    if discovered.is_error():
        from ppi.rop.errors import ValidationFailure

        return Error(
            ValidationFailure(
                stage="discover_artifacts",
                message=str(discovered.error),
                safe_input_id=str(addons_paths),
            )
        )
    return Ok(discovered.default_value(None))


def enrich_modules_stage(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, TypedStageError]:
    """Enrich modules with code analysis (metrics, complexity, AST facts)."""
    return Ok(enrich_modules_with_code_analysis(artifacts))


def attach_providers_stage(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, TypedStageError]:
    """Build owner/provider indexes from analyzed modules."""
    from ppi.core.odoo.pipeline import attach_provider_maps

    return Ok(attach_provider_maps(artifacts))


def attach_edges_stage(
    artifacts: AnalysisArtifacts,
) -> StageResult[AnalysisArtifacts, TypedStageError]:
    """Build cross-module edges and score aggregates."""
    from ppi.core.odoo.pipeline import attach_edges_and_scores

    return Ok(attach_edges_and_scores(artifacts))


def freeze_and_export_stage(
    artifacts: AnalysisArtifacts,
    commit: CommitRef,
) -> StageResult[AnalysisBatch, TypedStageError]:
    """Freeze artifacts into the analysis batch contract."""
    from ppi.core.analysis_mappers import artifacts_to_analysis_batch

    return Ok(artifacts_to_analysis_batch(artifacts, commit))


def odoo_project_analysis_pipeline(
    worktree_path: Path,
    commit: CommitRef,
    *,
    profile: str,
    addons_paths: tuple[Path, ...],
    report_config: ReportConfig | None = None,
) -> Result[AnalysisBatch, AnalysisError]:
    """Run the full Odoo analysis pipeline through typed ROP stages.

    This is the migrated entrypoint. Every stage is a named function
    with typed success/failure contracts.
    """
    from ppi.core.analyzer import analysis_profile_of, _SUPPORTED_PROFILES
    from ppi.core.errors import UnsupportedProfile

    if analysis_profile_of(profile) is None:
        return Error(UnsupportedProfile(actual=profile, supported=_SUPPORTED_PROFILES))

    try:
        config = report_config or report_config_stage(
            project_label=worktree_path.name,
            all_modules=True,
        )

        validated = resolve_and_validate_addons_stage(addons_paths)
        if validated.is_error():
            return Error(
                _map_validation_to_analysis_error(validated.error)
            )

        discovered = discover_artifacts_stage(config, validated.default_value(None))
        if discovered.is_error():
            return Error(
                _map_validation_to_analysis_error(discovered.error)
            )

        artifacts = discovered.default_value(None)
        enriched = enrich_modules_stage(artifacts)
        if enriched.is_error():
            return Error(
                _map_validation_to_analysis_error(enriched.error)
            )

        with_providers = attach_providers_stage(enriched.default_value(None))
        if with_providers.is_error():
            return Error(
                _map_validation_to_analysis_error(with_providers.error)
            )

        with_edges = attach_edges_stage(with_providers.default_value(None))
        if with_edges.is_error():
            return Error(
                _map_validation_to_analysis_error(with_edges.error)
            )

        batch = freeze_and_export_stage(with_edges.default_value(None), commit)
        if batch.is_error():
            return Error(
                _map_validation_to_analysis_error(batch.error)
            )

        return Ok(batch.default_value(None))

    except Exception as exc:
        return Error(PipelineUnexpectedError(message=str(exc)))


def _map_validation_to_analysis_error(
    err: TypedStageError,
) -> AnalysisError:
    """Map typed ROP errors back to the existing AnalysisError union.

    ponytail: preserves the current CLI contract; remove when all callers
    consume ``TypedStageError`` directly.
    """
    from ppi.core.errors import InvalidAddonsPath, ManifestDiscoveryError, PipelineUnexpectedError

    msg = err.message
    from ppi.rop.errors import ValidationFailure

    if isinstance(err, ValidationFailure):
        if "No matching" in msg or "manifest" in msg.lower():
            return ManifestDiscoveryError(addons_paths=())
        if "Invalid" in msg or "path" in msg.lower():
            return InvalidAddonsPath(paths=(msg,))
    return PipelineUnexpectedError(message=msg)
