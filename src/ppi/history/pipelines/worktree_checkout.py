"""Worktree prepare and checkout effect adapters.

Wraps Git worktree operations into ``StageResult`` adapters.
"""

from __future__ import annotations

from pathlib import Path

from expression.core.result import Error, Ok

from ppi.rop.errors import OrchestrationFailure
from ppi.rop.types import StageResult


def worktree_checkout_pipeline(
    repo_path: Path,
    worktree_dir: Path,
    commit_hash: str,
) -> StageResult[Path, OrchestrationFailure]:
    """Spec-named pipeline: checkout a commit to a worktree."""
    return worktree_prepare_adapter(repo_path, worktree_dir, commit_hash)


def worktree_prepare_adapter(
    repo_path: Path,
    worktree_dir: Path,
    commit_hash: str,
) -> StageResult[Path, OrchestrationFailure]:
    """Check out a specific commit into a worktree directory.

    Uses ``git worktree add`` to create a detached worktree.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree_dir), commit_hash],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )
        if result.returncode != 0:
            return Error(
                OrchestrationFailure(
                    stage="worktree_prepare",
                    message=result.stderr.strip(),
                    safe_input_id=str(worktree_dir),
                )
            )
        return Ok(worktree_dir)
    except FileNotFoundError:
        return Error(
            OrchestrationFailure(
                stage="worktree_prepare",
                message="Git executable not found",
                safe_input_id=str(repo_path),
            )
        )


def worktree_cleanup_adapter(
    worktree_dir: Path,
) -> StageResult[None, OrchestrationFailure]:
    """Remove a worktree directory after use."""
    import shutil

    try:
        shutil.rmtree(worktree_dir, ignore_errors=True)
        return Ok(None)
    except OSError as exc:
        return Error(
            OrchestrationFailure(
                stage="worktree_cleanup",
                message=str(exc),
                safe_input_id=str(worktree_dir),
                cause=exc,
            )
        )
