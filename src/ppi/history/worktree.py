"""Isolated git worktree lifecycle management.

Refactored to use pure command builders from :mod:`ppi.history.git_plan` via
the adapter helpers in :mod:`ppi.history.git`. No inline git-arg string
assembly remains; only ``run_git_command`` is called with a typed
:class:`GitCommand`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from expression.core.result import Error, Ok, Result

from ppi.history import git
from ppi.history.git_plan import GitCommand
from ppi.runtime.paths import worktree_path as default_worktree_path


def _run(command: GitCommand) -> Result[None, str]:
    """Run a git command, surfacing a string error for the legacy API."""
    result = git.run_git_command(command)
    if result.is_error():
        from ppi.history.value_objects import format_git_failure

        return Error(format_git_failure(result.error))  # type: ignore[union-attr]
    return Ok(None)


def ensure_worktree(
    repo_path: Path,
    branch: str,
    analysis_dir: Path,
) -> Result[Path, str]:
    """Create or reuse a detached worktree at the branch tip."""
    target = default_worktree_path(analysis_dir)
    if target.exists():
        cleanup = remove_worktree(repo_path, analysis_dir)
        if cleanup.is_error():
            return cleanup
    target.parent.mkdir(parents=True, exist_ok=True)
    created = _run(git.add_worktree_command(repo_path, target, branch))
    if created.is_error():
        return created
    return Ok(target)


def checkout_commit(worktree: Path, commit_hash: str) -> Result[None, str]:
    """Check out one commit silently inside the worktree."""
    return _run(git.checkout_commit_command(worktree, commit_hash))


def remove_worktree(repo_path: Path, analysis_dir: Path) -> Result[None, str]:
    """Remove the project's worktree directory."""
    target = default_worktree_path(analysis_dir)
    if not target.exists():
        return Ok(None)
    removed = _run(git.remove_worktree_command(repo_path, target))
    if removed.is_error():
        shutil.rmtree(target, ignore_errors=True)
        _run(git.prune_worktrees_command(repo_path))
    return Ok(None)
