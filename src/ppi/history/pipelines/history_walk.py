"""Commit iteration railway and per-commit error policy.

Defines the commit walk pipeline that iterates over a history plan,
checking out each commit, running the analysis, and collecting results.
"""

from __future__ import annotations

from pathlib import Path

from expression.core.result import Error, Ok

from ppi.core.contracts import AnalysisBatch, CommitRef
from ppi.core.odoo.pipeline import ReportConfig
from ppi.history.pipelines.history_plan import CommitPlanEntry, HistoryPlan
from ppi.history.pipelines.worktree_checkout import (
    worktree_cleanup_adapter,
    worktree_prepare_adapter,
)
from ppi.rop.errors import OrchestrationFailure
from ppi.rop.types import StageResult


def build_commit_ref(
    commit_entry: CommitPlanEntry,
) -> CommitRef:
    """Build a CommitRef from a plan entry (pure)."""
    return CommitRef(
        commit_hash=commit_entry.commit_hash,
        commit_order=commit_entry.commit_order,
        author_name="",
        author_email="",
        authored_at=0,
        committed_at=0,
        summary="",
    )


def per_commit_analysis_adapter(
    repo_path: Path,
    commit_entry: CommitPlanEntry,
    worktree_base: Path,
    *,
    profile: str = "odoo",
    addons_paths: tuple[Path, ...] | None = None,
    report_config: ReportConfig | None = None,
) -> StageResult[AnalysisBatch | None, OrchestrationFailure]:
    """Process one commit through checkout + analysis + cleanup.

    Returns ``Ok(AnalysisBatch)`` on success,
    ``Ok(None)`` when the commit is skipped (skip-with-report policy),
    or ``Error(OrchestrationFailure)`` on abort.
    """
    from ppi.core.pipelines.odoo_project import odoo_project_analysis_pipeline

    worktree_dir = worktree_base / commit_entry.commit_hash[:12]
    checkout = worktree_prepare_adapter(repo_path, worktree_dir, commit_entry.commit_hash)
    if checkout.is_error():
        return Error(checkout.error)

    try:
        commit_ref = build_commit_ref(commit_entry)
        resolved_addons = addons_paths if addons_paths is not None else (worktree_dir,)
        result = odoo_project_analysis_pipeline(
            worktree_dir,
            commit_ref,
            profile=profile,
            addons_paths=resolved_addons,
            report_config=report_config,
        )

        if result.is_error():
            return Ok(None)

        return Ok(result.default_value(None))
    finally:
        worktree_cleanup_adapter(worktree_dir)


def history_walk_analysis_pipeline(
    repo_path: Path,
    worktree_base: Path,
    plan: HistoryPlan,
    fail_fast: bool = False,
    *,
    profile: str = "odoo",
    addons_paths: tuple[Path, ...] | None = None,
    report_config: ReportConfig | None = None,
) -> StageResult[list[AnalysisBatch | None], OrchestrationFailure]:
    """Spec-named pipeline: walk commits and run analysis."""
    return commit_iteration_pipeline(
        repo_path, worktree_base, plan, fail_fast,
        profile=profile, addons_paths=addons_paths, report_config=report_config,
    )


def commit_iteration_pipeline(
    repo_path: Path,
    worktree_base: Path,
    plan: HistoryPlan,
    fail_fast: bool = False,
    *,
    profile: str = "odoo",
    addons_paths: tuple[Path, ...] | None = None,
    report_config: ReportConfig | None = None,
) -> StageResult[list[AnalysisBatch | None], OrchestrationFailure]:
    """Walk through the commit plan, running analysis per commit.

    Error policy:
    - ``fail_fast=True``: first failure aborts the entire walk.
    - ``fail_fast=False``: failures are recorded as ``None`` and the
      walk continues (skip-with-report).
    """
    results: list[AnalysisBatch | None] = []
    for entry in plan.commits:
        batch = per_commit_analysis_adapter(
            repo_path, entry, worktree_base,
            profile=profile, addons_paths=addons_paths, report_config=report_config,
        )
        if batch.is_error():
            if fail_fast:
                return Error(batch.error)
            results.append(None)
        else:
            results.append(batch.default_value(None))
    return Ok(results)
