"""Error-injection tests for Ibis query execution failures."""

from __future__ import annotations

from pathlib import Path

from ppi.storage.ibis_backend import connect_ibis


def test_ibis_connect_nonexistent_store() -> None:
    result = connect_ibis(Path("/nonexistent/store.duckdb"))
    assert result.is_error()
