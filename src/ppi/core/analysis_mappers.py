"""Pure mappers from pipeline domain artifacts to ``ppi.core.contracts`` DTOs.

These functions do not touch the filesystem or run the pipeline; they map
already-built :class:`AnalysisArtifacts` (and its parts) into the serializable
``AnalysisBatch`` contract. Mapping is testable on synthetic snapshots without
git/DuckDB/FastAPI.

The ``complexity is None`` branch in the legacy ``_file_metrics`` is replaced
by pattern matching over a typed :class:`ComplexityPresence` variant.

Edges are mapped from immutable :class:`CouplingEdgeSnapshot` (F1) and modules
from immutable :class:`ModuleFacts` via :func:`freeze_module_info` (F9). No
``object``/``type:ignore`` holes at the boundary (F10).
"""

from __future__ import annotations

from dataclasses import dataclass

from ppi.core.contracts import (
    AnalysisBatch,
    CommitRef,
    CouplingEdge,
    Distribution,
    EdgeBreakdown,
    Evidence,
    FailureRecord,
    FileMetrics,
    ModuleAggregate,
)
from ppi.core.odoo.complexity import ComplexityMetrics
from ppi.core.odoo.dist_stats import DistributionStats
from ppi.core.odoo.facts import CouplingEdgeSnapshot
from ppi.core.odoo.pipeline import (
    AnalysisArtifacts,
    FileComplexityInfo,
    FileLineInfo,
    file_top_folder,
)
from ppi.core.odoo.snapshots import ModuleFacts, freeze_module_info

__all__ = [
    "ComplexityPresence",
    "distribution_from_stats",
    "module_to_file_metrics",
    "module_to_failures",
    "module_to_aggregate",
    "edge_snapshot_to_contract",
    "artifacts_to_batch_parts",
    "artifacts_to_analysis_batch",
    "in_scope_manifest_depends",
]

_EMPTY_DISTRIBUTION = Distribution(count=0, mean=0.0, median=0.0, p95=0.0, max=0.0)


def distribution_from_stats(stats: DistributionStats) -> Distribution:
    """Map pipeline distribution stats to a contract Distribution."""
    return Distribution(
        count=stats.count,
        mean=stats.mean,
        median=stats.median,
        p95=stats.p95,
        max=stats.max,
    )


# --- Complexity presence variant (replaces ``complexity is None`` if-chain) -


@dataclass(frozen=True, slots=True)
class Missing:
    """No complexity data available for a file."""


@dataclass(frozen=True, slots=True)
class Present:
    """Complexity data present for a file."""

    metrics: ComplexityMetrics


ComplexityPresence = Missing | Present


def _resolve_complexity(
    file_info: FileLineInfo,
    complexity_file: FileComplexityInfo | None,
) -> ComplexityPresence:
    """Resolve the effective complexity for a file as a typed variant."""
    complexity = file_info.complexity
    if complexity is None and complexity_file is not None:
        complexity = complexity_file.complexity
    if complexity is None:
        return Missing()
    return Present(complexity)


def _distributions_for(
    presence: ComplexityPresence,
) -> tuple[Distribution, Distribution, Distribution]:
    """Return (cyclomatic, cognitive, jones) distributions for a presence variant."""
    match presence:
        case Missing():
            return _EMPTY_DISTRIBUTION, _EMPTY_DISTRIBUTION, _EMPTY_DISTRIBUTION
        case Present(metrics):
            return (
                distribution_from_stats(metrics.cyclomatic),
                distribution_from_stats(metrics.cognitive),
                distribution_from_stats(metrics.jones),
            )
        case _:
            return _EMPTY_DISTRIBUTION, _EMPTY_DISTRIBUTION, _EMPTY_DISTRIBUTION


# --- Module -> contracts ---------------------------------------------------


def in_scope_manifest_depends(module: ModuleFacts, module_names: set[str]) -> tuple[str, ...]:
    """Return manifest dependencies limited to the analyzed module set."""
    return tuple(sorted(dep for dep in module.manifest_depends if dep in module_names))


def module_to_file_metrics(
    module_name: str,
    module: ModuleFacts,
) -> tuple[FileMetrics, ...]:
    """Map one module's files to a tuple of ``FileMetrics`` (pure)."""
    complexity_lookup = {item.relative_path: item for item in module.python_complexity_files}
    out: list[FileMetrics] = []
    for file_info in module.files:
        complexity_file = complexity_lookup.get(file_info.relative_path)
        presence = _resolve_complexity(file_info, complexity_file)
        cyclomatic, cognitive, jones = _distributions_for(presence)
        out.append(
            FileMetrics(
                module_name=module_name,
                relative_path=file_info.relative_path,
                category=file_info.category,
                lines=file_info.lines,
                function_count=complexity_file.function_count if complexity_file else 0,
                jones_line_count=complexity_file.jones_line_count if complexity_file else 0,
                cyclomatic=cyclomatic,
                cognitive=cognitive,
                jones=jones,
                top_folder=file_top_folder(file_info.relative_path),
                parse_error=file_info.parse_error,
            )
        )
    return tuple(out)


def module_to_failures(
    module_name: str,
    module: ModuleFacts,
    commit_hash: str,
) -> tuple[FailureRecord, ...]:
    """Map one module's parse errors to ``FailureRecord`` tuple (pure)."""
    out: list[FailureRecord] = []
    for file_info in module.files:
        if file_info.parse_error:
            out.append(
                FailureRecord(
                    commit_hash=commit_hash,
                    file_path=f"{module_name}/{file_info.relative_path}",
                    error_text=file_info.parse_error,
                )
            )
    return tuple(out)


def module_to_aggregate(
    module_name: str,
    module: ModuleFacts,
    module_scores: dict[str, dict[str, int]],
    module_names: set[str],
) -> ModuleAggregate:
    """Map one module to a ``ModuleAggregate`` (pure)."""
    scores = module_scores.get(module_name, {"outgoing_score": 0, "incoming_score": 0})
    return ModuleAggregate(
        module_name=module_name,
        total_lines=module.total_lines,
        line_categories=dict(module.line_categories()),
        cyclomatic=distribution_from_stats(module.complexity.cyclomatic),
        cognitive=distribution_from_stats(module.complexity.cognitive),
        jones=distribution_from_stats(module.complexity.jones),
        declared_models_count=len(module.declared_models),
        inherited_models_count=len(module.inherited_models),
        python_complexity_parse_errors=module.python_complexity_parse_errors,
        score_out=scores.get("outgoing_score", 0),
        score_in=scores.get("incoming_score", 0),
        python_file_count=len(module.python_complexity_files),
        declared_models=tuple(sorted(module.declared_models)),
        inherited_models=tuple(sorted(module.inherited_models)),
        manifest_depends=in_scope_manifest_depends(module, module_names),
    )


# --- Edges -> contracts ----------------------------------------------------


def edge_snapshot_to_contract(snapshot: CouplingEdgeSnapshot) -> CouplingEdge:
    """Map one :class:`CouplingEdgeSnapshot` to a ``CouplingEdge`` (pure)."""
    bd = snapshot.breakdown
    return CouplingEdge(
        source_module=snapshot.source_module.value,
        target_module=snapshot.target_module.value,
        score=snapshot.score,
        kinds=snapshot.kinds_map,
        breakdown=EdgeBreakdown(
            model_reuse=bd.model_reuse,
            extension_or_method=bd.extension_or_method,
            view=bd.view,
            field_property=bd.field_property,
            total=bd.total,
        ),
        evidence=tuple(
            Evidence(
                kind=fact.kind.value,
                file_path=fact.file_path.value,
                line=int(fact.line) if fact.line is not None else 0,
                detail=fact.detail,
                source_quote=fact.source_quote,
            )
            for fact in snapshot.evidence
        ),
    )


def artifacts_to_batch_parts(
    artifacts: AnalysisArtifacts,
    commit: CommitRef,
) -> tuple[
    tuple[FileMetrics, ...],
    tuple[ModuleAggregate, ...],
    tuple[CouplingEdge, ...],
    tuple[FailureRecord, ...],
]:
    """Map full artifacts to (files, modules, edges, failures) tuples (pure).

    Modules are frozen to :class:`ModuleFacts` at this boundary (F9) so
    downstream mapping never touches mutable builders; edges come straight from
    the immutable :class:`CouplingEdgeSnapshot` stream (F1).
    """
    module_names = set(artifacts.modules)
    files: list[FileMetrics] = []
    modules: list[ModuleAggregate] = []
    failures: list[FailureRecord] = []
    for module_name, module in sorted(artifacts.modules.items()):
        facts = freeze_module_info(module)
        files.extend(module_to_file_metrics(module_name, facts))
        failures.extend(module_to_failures(module_name, facts, commit.commit_hash))
        modules.append(
            module_to_aggregate(module_name, facts, artifacts.module_scores, module_names)
        )

    edges = tuple(
        edge_snapshot_to_contract(snapshot)
        for snapshot in artifacts.edge_snapshots
        if snapshot.score > 0 or snapshot.kind_counts
    )
    return tuple(files), tuple(modules), edges, tuple(failures)


def artifacts_to_analysis_batch(artifacts: AnalysisArtifacts, commit: CommitRef) -> AnalysisBatch:
    """Map full artifacts to a complete ``AnalysisBatch`` (pure)."""
    files, modules, edges, failures = artifacts_to_batch_parts(artifacts, commit)
    return AnalysisBatch(
        commit=commit,
        files=files,
        modules=modules,
        edges=edges,
        failures=failures,
    )
