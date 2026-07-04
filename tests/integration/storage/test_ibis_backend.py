"""Tests for Ibis backend binding over fixture history stores."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import duckdb

from ppi.storage.ibis_backend import connect_ibis, disconnect_ibis


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
