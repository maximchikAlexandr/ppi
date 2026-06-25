"""Built-in analyzer provider for Odoo worktree analysis.

Split into:

* :func:`run_odoo_pipeline` — orchestration runner returning a typed
  ``Result[AnalysisBatch, AnalysisError]``. Mapping is delegated to
  :mod:`ppi.core.analysis_mappers`.
* :func:`analyze_worktree` — backwards-compatible wrapper preserving the legacy
  ``Result[AnalysisBatch, str]`` signature used by callers/CLI.
* :func:`report_config_to_scope` — thin scope mapper.
"""

from __future__ import annotations

from pathlib import Path

from expression.core.result import Error, Ok, Result
from toolz import pipe

from ppi.core.analysis_mappers import artifacts_to_analysis_batch
from ppi.core.contracts import (
    AnalysisBatch,
    AnalysisScope,
    CommitRef,
)
from ppi.core.errors import (
    AnalysisError,
    InvalidAddonsPath,
    ManifestDiscoveryError,
    PipelineUnexpectedError,
    UnsupportedProfile,
)
from ppi.core.odoo.pipeline import (
    ReportConfig,
    attach_edges_and_scores,
    attach_provider_maps,
    build_report_config,
    discover_analysis_artifacts,
    enrich_modules_with_code_analysis,
    resolve_addons_paths,
    validate_addons_paths,
)

__all__ = [
    "run_odoo_pipeline",
    "analyze_worktree",
    "report_config_to_scope",
    "AnalysisProfile",
    "AnalysisProfileRaw",
    "analysis_profile_of",
]

_SUPPORTED_PROFILES: tuple[str, ...] = ("odoo",)


class AnalysisProfile(str):
    """Typed analysis profile (currently only ``odoo``)."""


def analysis_profile_of(value: str) -> AnalysisProfile | None:
    """Parse a profile string into a typed profile, ``None`` if unsupported."""
    return AnalysisProfile(value) if value in _SUPPORTED_PROFILES else None


AnalysisProfileRaw = str


def _format_analysis_error(err: AnalysisError) -> str:
    """Format a typed analysis error as a single human-readable line.

    Used at the CLI/API boundary so the legacy ``Result[..., str]`` callers keep
    working; the domain only carries the typed union.
    """
    match err:
        case UnsupportedProfile(actual=actual, supported=supported):
            return f"Unsupported analysis profile: {actual} (supported: {', '.join(supported)})"
        case InvalidAddonsPath(paths=paths):
            return "Invalid addons paths:\n" + "\n".join(paths)
        case ManifestDiscoveryError(addons_paths=paths):
            return "No matching Odoo modules found under:\n" + "\n".join(paths)
        case PipelineUnexpectedError(message=message):
            return message
        case _:
            return str(err)


def run_odoo_pipeline(
    worktree_path: Path,
    commit: CommitRef,
    *,
    profile: AnalysisProfileRaw,
    addons_paths: tuple[Path, ...],
    report_config: ReportConfig | None = None,
) -> Result[AnalysisBatch, AnalysisError]:
    """Run the Odoo analysis pipeline returning a typed ``AnalysisError``.

    Orchestration only: pure mapping lives in :mod:`ppi.core.analysis_mappers`.
    Profile selection uses typed dispatch via :func:`analysis_profile_of`.

    No ``ValueError`` string matching (F2): typed errors come back as
    ``Result.Error`` from the pipeline stages; only truly unexpected
    exceptions are wrapped in :class:`PipelineUnexpectedError`.
    """
    if analysis_profile_of(profile) is None:
        return Error(UnsupportedProfile(actual=profile, supported=_SUPPORTED_PROFILES))
    try:
        config = report_config or build_report_config(
            project_label=worktree_path.name,
            all_modules=True,
        )
        resolved = resolve_addons_paths(addons_paths)
        validated = validate_addons_paths(resolved)
        if validated.is_error():
            return validated  # type: ignore[return-value]
        discovered = discover_analysis_artifacts(config, validated.default_value(None))  # type: ignore[union-attr,arg-type]
        if discovered.is_error():
            return discovered  # type: ignore[return-value]
        artifacts = pipe(
            discovered.default_value(None),  # type: ignore[union-attr,arg-type]
            enrich_modules_with_code_analysis,
            attach_provider_maps,
            attach_edges_and_scores,
        )
    except Exception as exc:  # noqa: BLE001
        return Error(PipelineUnexpectedError(message=str(exc)))

    return Ok(artifacts_to_analysis_batch(artifacts, commit))


def analyze_worktree(
    worktree_path: Path,
    commit: CommitRef,
    *,
    profile: str,
    addons_paths: tuple[Path, ...],
    report_config: ReportConfig | None = None,
) -> Result[AnalysisBatch, str]:
    """Run the Odoo analysis pipeline on a checked-out worktree path.

    Backwards-compatible wrapper around :func:`run_odoo_pipeline` that surfaces
    a plain string error for the legacy ``Result[AnalysisBatch, str]`` callers.
    """
    result = run_odoo_pipeline(
        worktree_path,
        commit,
        profile=profile,
        addons_paths=addons_paths,
        report_config=report_config,
    )
    if result.is_error():
        return Error(_format_analysis_error(result.error))  # type: ignore[union-attr]
    return Ok(result.default_value(None))  # type: ignore[union-attr, arg-type, return-value]


def report_config_to_scope(config: ReportConfig) -> AnalysisScope:
    """Map a pipeline report config to a persisted analysis scope."""
    return AnalysisScope(
        project_label=config.project_label,
        module_prefixes=config.module_prefixes,
        include_modules=config.include_modules,
        all_modules=config.all_modules,
    )
