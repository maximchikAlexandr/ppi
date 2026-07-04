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
from typing import Any

from ppi.core.value_objects import RelativeFilePath, SourceLine


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    GIT_ERROR = "GIT_ERROR"
    FILESYSTEM_ERROR = "FILESYSTEM_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    LOCK_ERROR = "LOCK_ERROR"
    QUERY_ERROR = "QUERY_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"


class ErrorCategory(StrEnum):
    VALIDATION = "validation"
    GIT = "git"
    FILESYSTEM = "filesystem"
    SCHEMA = "schema"
    LOCK = "lock"
    QUERY = "query"
    STORAGE = "storage"
    RUNTIME = "runtime"


@dataclass(frozen=True, slots=True)
class DomainError:
    code: ErrorCode
    category: ErrorCategory
    message: str
    stage: str = ""
    details: tuple[tuple[str, Any], ...] = ()
    cause: BaseException | None = None

    @staticmethod
    def with_details(code: ErrorCode, category: ErrorCategory, message: str, **details: Any) -> DomainError:
        return DomainError(
            code=code,
            category=category,
            message=message,
            details=tuple(sorted(details.items())),
        )


__all__ = [
    "ErrorCode",
    "ErrorCategory",
    "DomainError",
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
    "format_non_fatal_failure",
]


@dataclass(frozen=True, slots=True)
class UnsupportedProfile:
    actual: str
    supported: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InvalidAddonsPath:
    paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ManifestDiscoveryError:
    addons_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PipelineUnexpectedError:
    message: str


AnalysisError = (
    UnsupportedProfile | InvalidAddonsPath | ManifestDiscoveryError | PipelineUnexpectedError
)


class NonFatalFailureKind(StrEnum):
    SOURCE_QUOTE_READ_FAILED = "source_quote_read_failed"
    MANIFEST_READ_FAILED = "manifest_read_failed"
    MANIFEST_PARSE_FAILED = "manifest_parse_failed"
    PYTHON_PARSE_FAILED = "python_parse_failed"
    COMPLEXITY_TOOL_FAILED = "complexity_tool_failed"


@dataclass(frozen=True, slots=True)
class _BaseFailure:
    path: RelativeFilePath | None
    message: str

    @property
    def kind(self) -> NonFatalFailureKind:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class SourceQuoteReadFailed(_BaseFailure):
    line: SourceLine | None = None

    @property
    def kind(self) -> NonFatalFailureKind:
        return NonFatalFailureKind.SOURCE_QUOTE_READ_FAILED


@dataclass(frozen=True, slots=True)
class ManifestReadFailed(_BaseFailure):
    @property
    def kind(self) -> NonFatalFailureKind:
        return NonFatalFailureKind.MANIFEST_READ_FAILED


@dataclass(frozen=True, slots=True)
class ManifestParseFailed(_BaseFailure):
    @property
    def kind(self) -> NonFatalFailureKind:
        return NonFatalFailureKind.MANIFEST_PARSE_FAILED


@dataclass(frozen=True, slots=True)
class PythonParseFailed(_BaseFailure):
    @property
    def kind(self) -> NonFatalFailureKind:
        return NonFatalFailureKind.PYTHON_PARSE_FAILED


@dataclass(frozen=True, slots=True)
class ComplexityToolFailed(_BaseFailure):
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
    path = _failure_path_text(failure)
    prefix = f"[{failure.kind.value}] {path}".strip()
    return f"{prefix}: {failure.message}" if prefix else failure.message
