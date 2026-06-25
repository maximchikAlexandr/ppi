"""History <-> core contracts mappers.

Keeps :mod:`ppi.history.git` focused on git plumbing/parsing while the boundary
mapping to :class:`ppi.core.contracts.CommitRef` lives here. This restores the
dependency direction: git adapter no longer imports :mod:`ppi.core.contracts`.
"""

from __future__ import annotations

from ppi.core.contracts import CommitRef
from ppi.history.git_parse import GitCommitInfo
from ppi.history.value_objects import CommitOrder

__all__ = ["to_commit_ref", "placeholder_commit_ref"]


def to_commit_ref(info: GitCommitInfo, commit_order: CommitOrder | int) -> CommitRef:
    """Convert typed git commit info to a serializable ``CommitRef`` contract."""
    order = int(commit_order) if isinstance(commit_order, CommitOrder) else int(commit_order)
    return CommitRef(
        commit_hash=info.commit_hash.value,
        commit_order=order,
        author_name=info.author_name,
        author_email=info.author_email.value,
        authored_at=int(info.authored_at),
        committed_at=int(info.committed_at),
        summary=info.summary,
    )


def placeholder_commit_ref(commit_hash: str, commit_order: int) -> CommitRef:
    """Build minimal commit metadata when git show fails (boundary helper)."""
    return CommitRef(
        commit_hash=commit_hash,
        commit_order=commit_order,
        author_name="",
        author_email="",
        authored_at=0,
        committed_at=0,
        summary="",
    )
