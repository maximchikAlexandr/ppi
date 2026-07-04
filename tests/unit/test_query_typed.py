"""Unit tests for query errors."""

from __future__ import annotations

from ppi.query.errors import QueryError


def test_query_error_construction():
    exc = QueryError("INVALID_PARAMS", "x required", http_status=422)
    assert exc.code == "INVALID_PARAMS"
    assert exc.message == "x required"
    assert exc.http_status == 422


def test_query_error_repr():
    exc = QueryError("LOCKED", "busy", http_status=409)
    assert repr(exc) == "QueryError(code='LOCKED', http_status=409)"
