"""History-layer domain value objects.

Replaces raw ``str``/``int`` carrying critical git identifiers with typed
value objects that guard their invariants. String/int conversion happens only
at the contract/serialization boundary (see :mod:`ppi.history.mappers`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

import deal

from ppi.core.value_objects import AbsolutePathText, CommitHash, ContractError

__all__ = [
    "CommitHash",
    "BranchName",
    "CommitOrder",
    "EpochSeconds",
    "AuthorEmail",
    "RepoPath",
    "WorktreePath",
    "AddonsPath",
    "BranchInput",
    "DefaultBranch",
    "ExplicitBranch",
    "HeadAlias",
    "GitFailure",
    "DetachedHead",
    "BranchNotFound",
    "GitCommandError",
    "GitExecutableMissing",
]


# ponytail: CommitHash is re-exported from ppi.core.value_objects to avoid the
# duplicate domain entity between core and history (F6). The two were identical
# hex-string value objects; there is now a single canonical definition.
_BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/\-]*$")


def _no_whitespace(value: str) -> bool:
    return not any(c.isspace() for c in value)


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and _BRANCH_RE.match(obj.value),
    message="value must be a non-empty branch ref",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class BranchName:
    """A resolved git branch name."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and _BRANCH_RE.match(value),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a branch name value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, int) and not isinstance(obj.value, bool) and obj.value >= 0,
    message="value must be a non-negative int",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class CommitOrder:
    """0-based position of a commit in the walked history (>= 0)."""

    value: int

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, int) and not isinstance(value, bool) and value >= 0,
        exception=ContractError,
    )
    def of(cls, value: int) -> Self:
        """Build a commit order value object."""
        return cls(value)

    def __int__(self) -> int:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, int) and not isinstance(obj.value, bool) and obj.value >= 0,
    message="value must be a non-negative int (epoch seconds)",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class EpochSeconds:
    """Unix epoch seconds (>= 0)."""

    value: int

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, int) and not isinstance(value, bool) and value >= 0,
        exception=ContractError,
    )
    def of(cls, value: int) -> Self:
        """Build an epoch-seconds value object."""
        return cls(value)

    @classmethod
    def parse(cls, value: str) -> Self | None:
        """Parse epoch seconds from a string, returning ``None`` if not numeric."""
        if value.lstrip("-").isdigit():
            n = int(value)
            if n >= 0:
                return cls(n)
        return None

    def __int__(self) -> int:
        return self.value


def _no_whitespace(value: str) -> bool:
    return not any(c.isspace() for c in value)


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and _no_whitespace(obj.value),
    message="value must be a non-empty email without whitespace",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class AuthorEmail:
    """Author email address (basic shape validation)."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and _no_whitespace(value),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build an author email value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and obj.value.startswith("/"),
    message="value must be a non-empty absolute repo path",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class RepoPath:
    """Absolute path to a git repository."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and value.startswith("/"),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a repo path value object from an absolute path string."""
        return cls(value)

    def as_text(self) -> AbsolutePathText:
        """Return the path as a typed absolute path text."""
        return AbsolutePathText.of(self.value)

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and obj.value.startswith("/"),
    message="value must be a non-empty absolute worktree path",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class WorktreePath:
    """Absolute path to a git worktree."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and value.startswith("/"),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a worktree path value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and obj.value.startswith("/"),
    message="value must be a non-empty absolute addons path",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class AddonsPath:
    """Absolute path to an addons root, must stay inside a worktree."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and value.startswith("/"),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build an addons path value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


# --- Branch input variant (PPI-060) ----------------------------------------


@dataclass(frozen=True, slots=True)
class DefaultBranch:
    """No explicit branch: resolve the current branch from the repo."""


@dataclass(frozen=True, slots=True)
class ExplicitBranch:
    """An explicit branch/ref name passed by the caller."""

    name: str


@dataclass(frozen=True, slots=True)
class HeadAlias:
    """The literal string ``"HEAD"``: resolve to the current branch name."""

    raw: str = "HEAD"


BranchInput = DefaultBranch | ExplicitBranch | HeadAlias


def branch_input_from_cli(branch: str | None) -> BranchInput:
    """Classify a CLI branch argument into a typed :class:`BranchInput`."""
    match branch:
        case None:
            return DefaultBranch()
        case "HEAD":
            return HeadAlias()
        case str() as name:
            return ExplicitBranch(name=name)


# --- Typed git failures ----------------------------------------------------


class GitFailureKind(StrEnum):
    """Discriminator for :class:`GitFailure` variants."""

    DETACHED_HEAD = "detached_head"
    BRANCH_NOT_FOUND = "branch_not_found"
    COMMAND_ERROR = "command_error"
    EXECUTABLE_MISSING = "executable_missing"


@dataclass(frozen=True, slots=True)
class DetachedHead:
    """Repository is in detached HEAD state; no branch name available."""

    kind: GitFailureKind = GitFailureKind.DETACHED_HEAD
    message: str = "Repository is in detached HEAD state; pass --branch explicitly"


@dataclass(frozen=True, slots=True)
class BranchNotFound:
    """A named branch could not be resolved."""

    branch: str
    kind: GitFailureKind = GitFailureKind.BRANCH_NOT_FOUND
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(self, "message", f"Branch not found: {self.branch}")


@dataclass(frozen=True, slots=True)
class GitCommandError:
    """A git command returned a non-zero exit code."""

    message: str
    kind: GitFailureKind = GitFailureKind.COMMAND_ERROR


@dataclass(frozen=True, slots=True)
class GitExecutableMissing:
    """The git executable was not found on PATH."""

    message: str = "git executable not found on PATH"
    kind: GitFailureKind = GitFailureKind.EXECUTABLE_MISSING


GitFailure = DetachedHead | BranchNotFound | GitCommandError | GitExecutableMissing


def format_git_failure(failure: GitFailure) -> str:
    """Render one git failure as a human-readable string (boundary helper)."""
    match failure:
        case (
            DetachedHead(message=message)
            | GitCommandError(message=message)
            | GitExecutableMissing(message=message)
            | BranchNotFound(message=message)
        ):
            return message
        case _:
            return str(failure)
