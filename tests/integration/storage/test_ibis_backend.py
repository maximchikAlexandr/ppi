"""Tests for Ibis backend binding over fixture history stores."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import duckdb

from ppi.storage.ibis_backend import connect_ibis, disconnect_backend, disconnect_ibis


def test_ibis_backend_can_connect() -> None:
    tmpdir = Path(tempfile.mkdtemp())
    store = tmpdir / "history.duckdb"
    try:
        conn = duckdb.connect(str(store))
        conn.execute("CREATE TABLE test (x INTEGER)")
        conn.execute("INSERT INTO test VALUES (42)")
        conn.close()
        result = connect_ibis(store)
        assert result.is_ok()
        disconnect_ibis(store)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_disconnect_backend_does_not_close_sibling_connection() -> None:
    tmpdir = Path(tempfile.mkdtemp())
    store = tmpdir / "history.duckdb"
    try:
        conn = duckdb.connect(str(store))
        conn.execute("CREATE TABLE test (x INTEGER)")
        conn.execute("INSERT INTO test VALUES (42)")
        conn.close()

        first = connect_ibis(store)
        second = connect_ibis(store)
        assert first.is_ok()
        assert second.is_ok()

        disconnect_backend(first.ok)

        table = second.ok.table("test")
        result = second.ok.execute(table)
        assert result.to_dict(orient="records") == [{"x": 42}]
        disconnect_backend(second.ok)
    finally:
        disconnect_ibis(store)
        shutil.rmtree(tmpdir, ignore_errors=True)
