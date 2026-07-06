"""Tests for structured worker error mapping."""
from __future__ import annotations

from ppi.worker_ipc.protocol import (
    WorkerError,
    WorkerErrorCode,
    make_error_response,
    make_success_response,
)


def test_make_error_response_default_recoverable_false() -> None:
    resp = make_error_response(
        request_id="req-1",
        code=WorkerErrorCode.INTERNAL_ERROR,
        message="boom",
    )
    assert resp.ok is False
    assert resp.error is not None
    assert resp.error.code == "INTERNAL_ERROR"
    assert resp.error.message == "boom"
    assert resp.error.recoverable is False
    assert resp.error.details == {}


def test_make_error_response_recoverable_true() -> None:
    resp = make_error_response(
        request_id="req-1",
        code=WorkerErrorCode.WORKER_BUSY,
        message="busy",
        recoverable=True,
    )
    assert resp.error.recoverable is True


def test_make_error_response_with_details() -> None:
    resp = make_error_response(
        request_id="req-1",
        code=WorkerErrorCode.INVALID_REQUEST,
        message="bad",
        details={"field": "x"},
    )
    assert resp.error.details == {"field": "x"}


def test_make_success_response_default_empty_result() -> None:
    resp = make_success_response("req-1")
    assert resp.ok is True
    assert resp.result == {}
    assert resp.error is None


def test_make_success_response_with_result() -> None:
    resp = make_success_response("req-1", {"foo": "bar"})
    assert resp.ok is True
    assert resp.result == {"foo": "bar"}


def test_worker_error_is_frozen() -> None:
    import pytest
    err = WorkerError(code="X", message="m", details={}, recoverable=False)
    with pytest.raises(Exception):
        err.code = "Y"
