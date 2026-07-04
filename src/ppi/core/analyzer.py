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
from ppi.core.odoo.pipeline import ReportConfig
from ppi.core.pipelines.odoo_project import odoo_project_analysis_pipeline

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
    """Run the Odoo analysis pipeline via the new staged railway.

    Delegates to :func:`odoo_project_analysis_pipeline` which composes
    named typed stages. This function remains as a convenience wrapper
    with the same signature for existing callers.
    """
    return odoo_project_analysis_pipeline(
        worktree_path,
        commit,
        profile=profile,
        addons_paths=addons_paths,
        report_config=report_config,
    )


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
