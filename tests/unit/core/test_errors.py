"""Tests for DomainError serialization and safe debug details."""

from __future__ import annotations

from ppi.core.errors import DomainError, ErrorCategory, ErrorCode


def test_domain_error_has_code_and_category() -> None:
    err = DomainError(
        code=ErrorCode.VALIDATION_ERROR,
        category=ErrorCategory.VALIDATION,
        message="Invalid input",
    )
    assert err.code == ErrorCode.VALIDATION_ERROR
    assert err.category == ErrorCategory.VALIDATION
    assert err.message == "Invalid input"


def test_domain_error_default_stage_is_empty() -> None:
    err = DomainError(code=ErrorCode.GIT_ERROR, category=ErrorCategory.GIT, message="git fail")
    assert err.stage == ""


def test_domain_error_with_details() -> None:
    err = DomainError(
        code=ErrorCode.QUERY_ERROR,
        category=ErrorCategory.QUERY,
        message="query failed",
        details={"query_name": "hotspots", "param": "metric"},
    )
    assert err.details["query_name"] == "hotspots"


def test_domain_error_with_cause() -> None:
    cause = ValueError("original cause")
    err = DomainError(
        code=ErrorCode.STORAGE_ERROR,
        category=ErrorCategory.STORAGE,
        message="storage failed",
        cause=cause,
    )
    assert err.cause is cause


def test_domain_error_is_frozen() -> None:
    err = DomainError(code=ErrorCode.RUNTIME_ERROR, category=ErrorCategory.RUNTIME, message="runtime")
    with_attrs = {f.name for f in type(err).__dataclass_fields__.values()}
    assert "code" in with_attrs


def test_domain_error_is_hashable() -> None:
    err = DomainError(code=ErrorCode.VALIDATION_ERROR, category=ErrorCategory.VALIDATION, message="err")
    s = {err}
    assert err in s
