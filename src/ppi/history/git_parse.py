"""Pure git output parsing with typed results and structural pattern matching.

Replaces the inline ``parts = output.ok.strip().split("\\x1f")`` and
``int(parts[3])`` in :mod:`ppi.history.git` with a testable pure parser that
returns typed :class:`GitCommitInfo` (using history value objects) or a typed
:class:`GitParseFailure`. No ``ValueError`` from ``int(...)`` escapes.
"""

from __future__ import annotations

from dataclasses import dataclass

from expression.core.result import Error, Ok, Result

from ppi.history.value_objects import AuthorEmail, CommitHash, EpochSeconds

__all__ = [
    "GitCommitInfo",
    "GitParseFailure",
    "GitParseError",
    "parse_git_show_commit",
    "parse_commit_list",
]


@dataclass(frozen=True, slots=True)
class GitCommitInfo:
    """Commit metadata parsed from git show output (typed value objects)."""

    commit_hash: CommitHash
    author_name: str
    author_email: AuthorEmail
    authored_at: EpochSeconds
    committed_at: EpochSeconds
    summary: str


class GitParseError:
    """Discriminator constants for git parse failure reasons."""

    WRONG_FIELD_COUNT = "wrong_field_count"
    EMPTY_OUTPUT = "empty_output"
    INVALID_HASH = "invalid_hash"
    INVALID_EPOCH = "invalid_epoch"
    INVALID_EMAIL = "invalid_email"


@dataclass(frozen=True, slots=True)
class GitParseFailure:
    """Typed parse failure for git show output."""

    reason: str
    message: str
    raw: str | None = None


def parse_commit_list(output: str) -> tuple[str, ...]:
    """Parse ``git rev-list`` output into a tuple of stripped commit hashes."""
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def parse_git_show_commit(raw: str) -> Result[GitCommitInfo, GitParseFailure]:
    """Parse ``git show -s --format=...`` output into a typed commit info.

    The format is six ``\\x1f``-separated fields:
    ``%H %an %ae %at %ct %s``. Uses ``match parts:`` for the six-field shape.
    """
    stripped = raw.strip()
    if not stripped:
        return Error(
            GitParseFailure(
                reason=GitParseError.EMPTY_OUTPUT,
                message="git show output is empty",
                raw=raw,
            )
        )
    parts = stripped.split("\x1f")
    match parts:
        case [hash_str, author_name, email_str, authored_str, committed_str, summary]:
            return _build_commit_info(
                hash_str, author_name, email_str, authored_str, committed_str, summary, raw
            )
        case _:
            return Error(
                GitParseFailure(
                    reason=GitParseError.WRONG_FIELD_COUNT,
                    message=f"Expected 6 fields, got {len(parts)}",
                    raw=raw,
                )
            )


def _build_commit_info(
    hash_str: str,
    author_name: str,
    email_str: str,
    authored_str: str,
    committed_str: str,
    summary: str,
    raw: str,
) -> Result[GitCommitInfo, GitParseFailure]:
    """Build a typed GitCommitInfo from six field strings, returning typed failure."""
    commit_hash = CommitHash.parse(hash_str)
    if commit_hash is None:
        return Error(
            GitParseFailure(
                reason=GitParseError.INVALID_HASH,
                message=f"Invalid commit hash: {hash_str!r}",
                raw=raw,
            )
        )
    authored = EpochSeconds.parse(authored_str)
    if authored is None:
        return Error(
            GitParseFailure(
                reason=GitParseError.INVALID_EPOCH,
                message=f"Invalid authored_at epoch: {authored_str!r}",
                raw=raw,
            )
        )
    committed = EpochSeconds.parse(committed_str)
    if committed is None:
        return Error(
            GitParseFailure(
                reason=GitParseError.INVALID_EPOCH,
                message=f"Invalid committed_at epoch: {committed_str!r}",
                raw=raw,
            )
        )
    try:
        email = AuthorEmail.of(email_str)
    except ValueError as exc:
        return Error(
            GitParseFailure(
                reason=GitParseError.INVALID_EMAIL,
                message=str(exc),
                raw=raw,
            )
        )
    return Ok(
        GitCommitInfo(
            commit_hash=commit_hash,
            author_name=author_name,
            author_email=email,
            authored_at=authored,
            committed_at=committed,
            summary=summary,
        )
    )
