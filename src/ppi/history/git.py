"""Git plumbing for history traversal.

Refactored into an adapter shell over the pure modules:

* :mod:`ppi.history.git_plan` — pure command builders (no subprocess).
* :mod:`ppi.history.git_parse` — pure output parsing with typed failures.
* :mod:`ppi.history.value_objects` — typed git identifiers.
* :mod:`ppi.history.mappers` — boundary mapping to core contracts.

This module only runs git commands and delegates parsing; it no longer
assembles command strings inline, hides ``int(...)`` parsing in control flow,
or imports :mod:`ppi.core.contracts` inside a function body. Public functions
preserve the legacy signatures so callers (CLI/walker/worktree/tests) keep
working.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from expression.core.result import Error, Ok, Result

from ppi.history.git_parse import GitCommitInfo, parse_commit_list, parse_git_show_commit
from ppi.history.git_plan import (
    GitCommand,
    cmd_add_worktree,
    cmd_checkout_commit,
    cmd_current_branch,
    cmd_git_version,
    cmd_list_non_merge_commits,
    cmd_prune_worktrees,
    cmd_remove_worktree,
    cmd_show_commit,
    cmd_verify_branch,
)
from ppi.history.mappers import to_commit_ref as _to_commit_ref_mapper
from ppi.history.value_objects import (
    BranchName,
    BranchNotFound,
    CommitHash,
    DefaultBranch,
    DetachedHead,
    ExplicitBranch,
    GitCommandError,
    GitExecutableMissing,
    GitFailure,
    HeadAlias,
    RepoPath,
    WorktreePath,
    branch_input_from_cli,
    format_git_failure,
)

__all__ = [
    "GitCommitInfo",
    "run_git",
    "run_git_command",
    "resolve_branch",
    "resolve_branch_typed",
    "list_non_merge_commits",
    "read_commit_info",
    "to_commit_ref",
    "git_version",
    "utc_now_epoch",
]


def run_git(repo_path: Path, *args: str) -> Result[str, str]:
    """Run a git command with captured output (legacy ``Result[str, str]`` API)."""
    command = GitCommand.of(str(repo_path), *args)
    result = run_git_command(command)
    if result.is_error():
        return Error(format_git_failure(result.error))  # type: ignore[union-attr]
    return Ok(result.default_value(""))  # type: ignore[union-attr, arg-type, return-value]


def run_git_command(command: GitCommand) -> Result[str, GitFailure]:
    """Execute a :class:`GitCommand` and return typed ``GitFailure`` on error."""
    try:
        completed = subprocess.run(
            command.full_args,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return Error(GitExecutableMissing())
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "git command failed").strip()
        return Error(GitCommandError(message=message))
    return Ok(completed.stdout)


def _current_branch_name(repo_path: Path) -> Result[str, GitFailure]:
    """Return the current branch name or :class:`DetachedHead` failure."""
    result = run_git_command(cmd_current_branch(RepoPath.of(str(repo_path.resolve()))))
    if result.is_error():
        return result
    name = result.default_value("").strip()  # type: ignore[union-attr]
    if name == "HEAD":
        return Error(DetachedHead())
    return Ok(name)


def resolve_branch_typed(repo_path: Path, branch: str | None) -> Result[str, GitFailure]:
    """Resolve a branch name returning typed :class:`GitFailure` (PPI-060)."""
    repo = RepoPath.of(str(repo_path.resolve()))
    match branch_input_from_cli(branch):
        case DefaultBranch():
            return _current_branch_name(repo_path)
        case HeadAlias():
            name_result = _current_branch_name(repo_path)
            if name_result.is_error():
                return name_result
            name = name_result.default_value("").strip()  # type: ignore[union-attr]
            if name == "HEAD":
                return Error(DetachedHead())
            return Ok(name)
        case ExplicitBranch(name=name):
            verify = run_git_command(cmd_verify_branch(repo, BranchName.of(name)))
            if verify.is_error():
                return Error(BranchNotFound(branch=name))
            return Ok(name)


def resolve_branch(repo_path: Path, branch: str | None) -> Result[str, str]:
    """Resolve branch name, defaulting to the current branch (legacy string API)."""
    result = resolve_branch_typed(repo_path, branch)
    if result.is_error():
        return Error(format_git_failure(result.error))  # type: ignore[union-attr]
    return Ok(result.default_value(""))  # type: ignore[union-attr, arg-type, return-value]


def list_non_merge_commits(repo_path: Path, branch: str) -> Result[list[str], str]:
    """List non-merge commits oldest to newest for one branch."""
    repo = RepoPath.of(str(repo_path.resolve()))
    result = run_git_command(cmd_list_non_merge_commits(repo, BranchName.of(branch)))
    if result.is_error():
        return Error(format_git_failure(result.error))  # type: ignore[union-attr]
    return Ok(list(parse_commit_list(result.default_value(""))))  # type: ignore[union-attr]


def read_commit_info(repo_path: Path, commit_hash: str) -> Result[GitCommitInfo, str]:
    """Read metadata for one commit hash, returning typed ``GitCommitInfo``.

    Pure parsing is delegated to :func:`ppi.history.git_parse.parse_git_show_commit`;
    this function only runs the git command and feeds stdout to the parser.
    """
    repo = RepoPath.of(str(repo_path.resolve()))
    commit = CommitHash.of(commit_hash)
    result = run_git_command(cmd_show_commit(repo, commit))
    if result.is_error():
        return Error(format_git_failure(result.error))  # type: ignore[union-attr]
    parse_result = parse_git_show_commit(result.default_value(""))  # type: ignore[union-attr]
    if parse_result.is_error():
        return Error(parse_result.error.message)  # type: ignore[union-attr]
    return Ok(parse_result.default_value(None))  # type: ignore[union-attr, arg-type, return-value]


def to_commit_ref(info: GitCommitInfo, commit_order: int):
    """Convert git metadata to a CommitRef contract (delegates to mappers)."""
    return _to_commit_ref_mapper(info, commit_order)


def git_version(repo_path: Path) -> Result[str, str]:
    """Return git version output."""
    repo = RepoPath.of(str(repo_path.resolve()))
    result = run_git_command(cmd_git_version(repo))
    if result.is_error():
        return Error(format_git_failure(result.error))  # type: ignore[union-attr]
    return Ok(result.default_value(""))  # type: ignore[union-attr, arg-type, return-value]


def utc_now_epoch() -> int:
    """Return current UTC time as epoch seconds."""
    return int(datetime.now(UTC).timestamp())


# Re-export command builders used by worktree.py so it can stay decoupled from
# inline string assembly while keeping its existing function-based API.
def add_worktree_command(repo_path: Path, target: Path, branch: str) -> GitCommand:
    """Build a ``git worktree add`` command (PPI-048)."""
    return cmd_add_worktree(
        RepoPath.of(str(repo_path.resolve())),
        WorktreePath.of(str(target.resolve())),
        branch,
    )


def checkout_commit_command(worktree: Path, commit_hash: str) -> GitCommand:
    """Build a ``git checkout`` command (PPI-048)."""
    return cmd_checkout_commit(
        WorktreePath.of(str(worktree.resolve())),
        CommitHash.of(commit_hash),
    )


def remove_worktree_command(repo_path: Path, target: Path) -> GitCommand:
    """Build a ``git worktree remove`` command (PPI-048)."""
    return cmd_remove_worktree(
        RepoPath.of(str(repo_path.resolve())),
        WorktreePath.of(str(target.resolve())),
    )


def prune_worktrees_command(repo_path: Path) -> GitCommand:
    """Build a ``git worktree prune`` command (PPI-048)."""
    return cmd_prune_worktrees(RepoPath.of(str(repo_path.resolve())))
