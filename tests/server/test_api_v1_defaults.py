"""Default-commit selection picks the greatest commitOrder, not lexicographic."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ppi.server.app import create_app


def test_default_commit_uses_greatest_commit_order(tmp_path: Path) -> None:
    """When no commit_id is provided, the resolver must pick commitOrder=3."""
    from ppi.server import api_v1

    rows = [
        {"commit_hash": "aaa", "commit_order": 1, "authored_at": None, "summary": "first"},
        {"commit_hash": "bbb", "commit_order": 2, "authored_at": None, "summary": "second"},
        {"commit_hash": "ccc", "commit_order": 3, "authored_at": None, "summary": "third"},
    ]

    class _FakeResult:
        def __init__(self, ok):
            self._ok = ok
        def is_ok(self):
            return True
        @property
        def ok(self):
            return self._ok

    def fake_run_query(store_file, params):
        if params.metric == "commits":
            return _FakeResult(rows)
        return _FakeResult(None)

    import ppi.query.pipeline as pipe

    orig = pipe.run_query
    pipe.run_query = fake_run_query
    try:
        chosen = pipe.resolve_commit(tmp_path / "x.duckdb", None)
    finally:
        pipe.run_query = orig

    assert chosen is not None
    assert chosen["commit_order"] == 3
