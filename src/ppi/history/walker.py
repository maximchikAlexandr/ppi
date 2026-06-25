"""History walk orchestration.

Refactored to use the typed :class:`AddonsScanRoots` invariant (PPI-051) and
the history plan/state-machine types (PPI-018/PPI-050) where helpful. The
public :func:`walk_history` stays an imperative generator/runner that calls
effect handlers; pure planning lives in :mod:`ppi.history.history_plan`.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from expression.core.result import Ok, Result

from ppi.core.analyzer import analyze_worktree
from ppi.core.contracts import AnalysisBatch, CommitRef, FailureRecord
from ppi.core.odoo.pipeline import ReportConfig
from ppi.history import git, worktree
from ppi.history.history_plan import AddonsScanRoots, build_history_plan
from ppi.history.mappers import placeholder_commit_ref


@dataclass(slots=True)
class WalkState:
    """Counters updated while walking history (legacy mutable counter carrier)."""

    commits_total: int


def _failure_batch(
    commit_ref: CommitRef,
    error_text: str,
) -> AnalysisBatch:
    """Build a batch that records one commit-level failure."""
    return AnalysisBatch(
        commit=commit_ref,
        files=(),
        modules=(),
        edges=(),
        failures=(
            FailureRecord(
                commit_hash=commit_ref.commit_hash,
                file_path=None,
                error_text=error_text,
            ),
        ),
    )


def _resolve_scan_roots(
    worktree_path: Path,
    addons_paths: tuple[str, ...],
) -> Result[tuple[Path, ...], str]:
    """Resolve addon scan roots via the typed :class:`AddonsScanRoots` invariant."""
    roots_result = AddonsScanRoots.from_cli(worktree_path, addons_paths)
    if roots_result.is_error():
        return roots_result
    return Ok(roots_result.default_value(None).as_paths())  # type: ignore[union-attr]


def walk_history(
    repo_path: Path,
    branch_name: str,
    analysis_dir: Path,
    *,
    profile: str = "odoo",
    skip_commits: set[str] | None = None,
    addons_paths: tuple[str, ...] = (),
    report_config: ReportConfig | None = None,
) -> Result[tuple[Iterator[AnalysisBatch], WalkState], str]:
    """Prepare a history walk over non-merge commits on a resolved branch."""
    commits_result = git.list_non_merge_commits(repo_path, branch_name)
    if commits_result.is_error():
        return commits_result
    all_commits = commits_result.ok
    plan = build_history_plan(all_commits, skip=skip_commits, profile=profile)
    wt_result = worktree.ensure_worktree(repo_path, branch_name, analysis_dir)
    if wt_result.is_error():
        return wt_result
    worktree_path = wt_result.ok
    roots_result = _resolve_scan_roots(worktree_path, addons_paths)
    if roots_result.is_error():
        return roots_result
    scan_roots = roots_result.ok
    state = WalkState(commits_total=len(plan.commits))

    def _iter() -> Iterator[AnalysisBatch]:
        for commit_hash in plan.commits:
            order = plan.order_by_hash[commit_hash]
            info_result = git.read_commit_info(repo_path, commit_hash)
            if info_result.is_error():
                yield _failure_batch(placeholder_commit_ref(commit_hash, order), info_result.error)
                continue
            commit_ref = git.to_commit_ref(info_result.ok, order)
            checkout = worktree.checkout_commit(worktree_path, commit_hash)
            if checkout.is_error():
                yield _failure_batch(commit_ref, checkout.error)
                continue
            batch_result = analyze_worktree(
                worktree_path,
                commit_ref,
                profile=profile,
                addons_paths=scan_roots,
                report_config=report_config,
            )
            if batch_result.is_error():
                yield _failure_batch(commit_ref, batch_result.error)
                continue
            yield batch_result.ok

    return Ok((_iter(), state))


def cleanup_worktree(repo_path: Path, analysis_dir: Path) -> None:
    """Remove the isolated worktree after a walk."""
    worktree.remove_worktree(repo_path, analysis_dir)
