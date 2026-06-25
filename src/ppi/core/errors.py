"""Typed analysis errors and non-fatal analysis failures.

Error model (see PPI-013/PPI-057/PPI-061):

* **Recoverable user/environment errors** -> ``AnalysisError`` union returned
  as a typed ``Result[AnalysisBatch, AnalysisError]`` from the runner. Never
  raised across the runner boundary.
* **Non-fatal analysis issues** (a file failed to parse, a manifest was
  unreadable) -> ``NonFatalAnalysisFailure`` value object collected alongside
  successful results so they surface in the UI/report instead of vanishing.
* **Programmer/system invariant violations** -> fail-fast ``ContractError``
  (see :mod:`ppi.core.contracts_runtime`); not part of this module.

``AnalysisError`` is a frozen union; callers use ``match``/``isinstance`` to
select transport behavior. String formatting lives in CLI/API layer, not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ppi.core.value_objects import RelativeFilePath, SourceLine

__all__ = [
    "UnsupportedProfile",
    "InvalidAddonsPath",
    "ManifestDiscoveryError",
    "PipelineUnexpectedError",
    "AnalysisError",
    "NonFatalAnalysisFailure",
    "SourceQuoteReadFailed",
    "ManifestReadFailed",
    "ManifestParseFailed",
    "PythonParseFailed",
    "ComplexityToolFailed",
    "NonFatalFailureKind",
]


# --- Recoverable analysis errors (returned as Result.Error) ----------------


@dataclass(frozen=True, slots=True)
class UnsupportedProfile:
    """The runner was asked to use an unsupported analysis profile."""

    actual: str
    supported: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InvalidAddonsPath:
    """One or more addons paths do not resolve to existing directories."""

    paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ManifestDiscoveryError:
    """Module discovery found no matching modules under the given paths."""

    addons_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PipelineUnexpectedError:
    """An unexpected exception escaped the pipeline (wrapped message)."""

    message: str


AnalysisError = (
    UnsupportedProfile | InvalidAddonsPath | ManifestDiscoveryError | PipelineUnexpectedError
)


# --- Non-fatal analysis failures (collected, never raised) -----------------


class NonFatalFailureKind(StrEnum):
    """Discriminator for :class:`NonFatalAnalysisFailure` variants."""

    SOURCE_QUOTE_READ_FAILED = "source_quote_read_failed"
    MANIFEST_READ_FAILED = "manifest_read_failed"
    MANIFEST_PARSE_FAILED = "manifest_parse_failed"
    PYTHON_PARSE_FAILED = "python_parse_failed"
    COMPLEXITY_TOOL_FAILED = "complexity_tool_failed"


@dataclass(frozen=True, slots=True)
class _BaseFailure:
    """Common fields for non-fatal analysis failures."""

    path: RelativeFilePath | None
    message: str

    @property
    def kind(self) -> NonFatalFailureKind:  # pragma: no cover - overridden
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class SourceQuoteReadFailed(_BaseFailure):
    """Could not read a source quote line from the filesystem."""

    line: SourceLine | None = None

    @property
    def kind(self) -> NonFatalFailureKind:
        return NonFatalFailureKind.SOURCE_QUOTE_READ_FAILED


@dataclass(frozen=True, slots=True)
class ManifestReadFailed(_BaseFailure):
    """Could not read a manifest file (OSError)."""

    @property
    def kind(self) -> NonFatalFailureKind:
        return NonFatalFailureKind.MANIFEST_READ_FAILED


@dataclass(frozen=True, slots=True)
class ManifestParseFailed(_BaseFailure):
    """Manifest could not be parsed as a dict literal."""

    @property
    def kind(self) -> NonFatalFailureKind:
        return NonFatalFailureKind.MANIFEST_PARSE_FAILED


@dataclass(frozen=True, slots=True)
class PythonParseFailed(_BaseFailure):
    """A Python source file failed to parse (SyntaxError/UnicodeDecodeError)."""

    @property
    def kind(self) -> NonFatalFailureKind:
        return NonFatalFailureKind.PYTHON_PARSE_FAILED


@dataclass(frozen=True, slots=True)
class ComplexityToolFailed(_BaseFailure):
    """A complexity library (radon/complexipy) failed on a file."""

    @property
    def kind(self) -> NonFatalFailureKind:
        return NonFatalFailureKind.COMPLEXITY_TOOL_FAILED


NonFatalAnalysisFailure = (
    SourceQuoteReadFailed
    | ManifestReadFailed
    | ManifestParseFailed
    | PythonParseFailed
    | ComplexityToolFailed
)


def _failure_path_text(failure: NonFatalAnalysisFailure) -> str:
    path = failure.path
    return path.value if path is not None else ""


def format_non_fatal_failure(failure: NonFatalAnalysisFailure) -> str:
    """Render one non-fatal failure as a single human-readable line.

    Used at the CLI/UI boundary; the domain keeps failures structured.
    """
    path = _failure_path_text(failure)
    prefix = f"[{failure.kind.value}] {path}".strip()
    return f"{prefix}: {failure.message}" if prefix else failure.message
