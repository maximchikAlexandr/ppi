"""Pure git command builders (no subprocess).

``GitCommand`` is a frozen value object carrying ``repo_path`` and ``args``.
Pure builder functions return ``GitCommand`` without touching the filesystem or
``subprocess``; the adapter (:func:`ppi.history.git.run_git`) only executes
them. This makes the string assembly of git commands testable in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass

from ppi.history.value_objects import BranchName, CommitHash, RepoPath, WorktreePath

__all__ = [
    "GitCommand",
    "cmd_current_branch",
    "cmd_verify_branch",
    "cmd_list_non_merge_commits",
    "cmd_show_commit",
    "cmd_add_worktree",
    "cmd_checkout_commit",
    "cmd_remove_worktree",
    "cmd_prune_worktrees",
    "cmd_git_version",
]


@dataclass(frozen=True, slots=True)
class GitCommand:
    """One git command to run: repo path + argument tuple.

    ``repo_path`` is the directory git runs in (``-C``); ``args`` excludes the
    leading ``git`` and ``-C <path>`` which the adapter adds.
    """

    repo_path: str
    args: tuple[str, ...]

    @classmethod
    def of(cls, repo_path: str, *args: str) -> GitCommand:
        """Build a git command value object."""
        return cls(repo_path=repo_path, args=tuple(args))

    @property
    def full_args(self) -> tuple[str, ...]:
        """Return the full argv tuple including ``git -C <path>``."""
        return ("git", "-C", self.repo_path, *self.args)


def cmd_current_branch(repo: RepoPath) -> GitCommand:
    """``git rev-parse --abbrev-ref HEAD``."""
    return GitCommand.of(repo.value, "rev-parse", "--abbrev-ref", "HEAD")


def cmd_verify_branch(repo: RepoPath, branch: BranchName) -> GitCommand:
    """``git rev-parse --verify <branch>``."""
    return GitCommand.of(repo.value, "rev-parse", "--verify", branch.value)


def cmd_list_non_merge_commits(repo: RepoPath, branch: BranchName) -> GitCommand:
    """``git rev-list --no-merges --reverse <branch>``."""
    return GitCommand.of(repo.value, "rev-list", "--no-merges", "--reverse", branch.value)


def cmd_show_commit(repo: RepoPath, commit: CommitHash) -> GitCommand:
    """``git show -s --format=... <commit>``."""
    return GitCommand.of(
        repo.value,
        "show",
        "-s",
        "--format=%H%x1f%an%x1f%ae%x1f%at%x1f%ct%x1f%s",
        commit.value,
    )


def cmd_add_worktree(repo: RepoPath, target: WorktreePath, branch: BranchName | str) -> GitCommand:
    """``git worktree add --detach <target> <branch>``."""
    branch_value = branch.value if isinstance(branch, BranchName) else branch
    return GitCommand.of(repo.value, "worktree", "add", "--detach", target.value, branch_value)


def cmd_checkout_commit(worktree: WorktreePath, commit: CommitHash) -> GitCommand:
    """``git checkout --detach --quiet --force <commit>``."""
    return GitCommand.of(worktree.value, "checkout", "--detach", "--quiet", "--force", commit.value)


def cmd_remove_worktree(repo: RepoPath, target: WorktreePath) -> GitCommand:
    """``git worktree remove --force <target>``."""
    return GitCommand.of(repo.value, "worktree", "remove", "--force", target.value)


def cmd_prune_worktrees(repo: RepoPath) -> GitCommand:
    """``git worktree prune``."""
    return GitCommand.of(repo.value, "worktree", "prune")


def cmd_git_version(repo: RepoPath) -> GitCommand:
    """``git --version``."""
    return GitCommand.of(repo.value, "--version")
