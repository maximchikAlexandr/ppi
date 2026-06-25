"""Runtime value objects: clock, run/project ids, analysis paths (PPI-058).

Replaces direct ``datetime.now(UTC)`` and ad-hoc path strings in domain/history
code with injectable providers and typed value objects, so tests do not depend
on system time or the user's home directory.

The existing :mod:`ppi.runtime.paths` functions stay as adapter helpers that
build these value objects; new domain code accepts a ``Clock``/path providers
explicitly instead of reaching for globals.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, Self

import deal

from ppi.core.value_objects import ContractError

__all__ = [
    "Clock",
    "SystemClock",
    "FakeClock",
    "RunId",
    "ProjectId",
    "AnalysisDir",
    "StorePath",
    "WriterLockPath",
    "WorktreeDir",
]


# --- Clock protocol --------------------------------------------------------


class Clock(Protocol):
    """Protocol for reading the current UTC time as epoch seconds."""

    def now_epoch(self) -> int: ...


class SystemClock:
    """Clock backed by the system wall clock."""

    def now_epoch(self) -> int:
        """Return current UTC time as epoch seconds."""
        return int(datetime.now(UTC).timestamp())


class FakeClock:
    """Deterministic clock for tests; returns a fixed or advancing epoch."""

    def __init__(self, initial: int = 0, *, advance_per_call: int = 0) -> None:
        self._value = initial
        self._advance = advance_per_call

    def now_epoch(self) -> int:
        """Return the current fake epoch, optionally advancing on each call."""
        current = self._value
        self._value += self._advance
        return current


# --- Typed identifiers -----------------------------------------------------


_RUN_ID_RE = re.compile(r"^[0-9a-fA-F]{8,64}$")
_PROJECT_ID_RE = re.compile(r"^[0-9a-fA-F]{16}$")


# ponytail: contracts via @deal.inv on the class + @deal.pre on the factory
# (F5/F6). No __post_init__ — the deal decorators carry the invariant as data.
@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and _RUN_ID_RE.match(obj.value),
    message="value must be a non-empty 8..64 hex string",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class RunId:
    """Identifier for one analyze invocation (hex)."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and _RUN_ID_RE.match(value),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a run id value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and _PROJECT_ID_RE.match(obj.value),
    message="value must be 16 hex chars",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class ProjectId:
    """Stable 16-hex-char project identifier derived from the repo path."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and _PROJECT_ID_RE.match(value),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a project id value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


# --- Typed analysis paths --------------------------------------------------


@deal.inv(
    lambda obj: isinstance(obj.value, Path) and obj.value.is_absolute(),
    message="value must be an absolute Path",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class AnalysisDir:
    """Absolute directory holding per-project analysis artifacts."""

    value: Path

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, (Path, str)),
        exception=ContractError,
    )
    def of(cls, path: Path | str) -> Self:
        """Build an analysis dir value object."""
        p = Path(path)
        if not p.is_absolute():
            raise ContractError(f"AnalysisDir must be absolute: {p}")
        return cls(p)

    def __str__(self) -> str:
        return str(self.value)


@deal.inv(
    lambda obj: isinstance(obj.value, Path) and obj.value.is_absolute(),
    message="value must be an absolute Path",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class StorePath:
    """Absolute path to the DuckDB store file."""

    value: Path

    @classmethod
    @deal.pre(lambda cls, value: isinstance(value, (Path, str)), exception=ContractError)
    def of(cls, path: Path | str) -> Self:
        """Build a store path value object."""
        p = Path(path)
        if not p.is_absolute():
            raise ContractError(f"StorePath must be absolute: {p}")
        return cls(p)

    def __str__(self) -> str:
        return str(self.value)


@deal.inv(
    lambda obj: isinstance(obj.value, Path) and obj.value.is_absolute(),
    message="value must be an absolute Path",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class WriterLockPath:
    """Absolute path to the writer lock file."""

    value: Path

    @classmethod
    @deal.pre(lambda cls, value: isinstance(value, (Path, str)), exception=ContractError)
    def of(cls, path: Path | str) -> Self:
        """Build a writer-lock path value object."""
        p = Path(path)
        if not p.is_absolute():
            raise ContractError(f"WriterLockPath must be absolute: {p}")
        return cls(p)

    def __str__(self) -> str:
        return str(self.value)


@deal.inv(
    lambda obj: isinstance(obj.value, Path) and obj.value.is_absolute(),
    message="value must be an absolute Path",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class WorktreeDir:
    """Absolute path to the isolated git worktree directory."""

    value: Path

    @classmethod
    @deal.pre(lambda cls, value: isinstance(value, (Path, str)), exception=ContractError)
    def of(cls, path: Path | str) -> Self:
        """Build a worktree dir value object."""
        p = Path(path)
        if not p.is_absolute():
            raise ContractError(f"WorktreeDir must be absolute: {p}")
        return cls(p)

    def __str__(self) -> str:
        return str(self.value)
