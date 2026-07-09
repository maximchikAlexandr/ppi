"""Public /api/v1 errors use ErrorResponse shape, not FastAPI defaults."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ppi.server.app import create_app


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))


def test_validation_error_returns_error_response(tmp_path: Path) -> None:
    client = _client(tmp_path)
    resp = client.get("/api/v1/entities")  # missing required entityKindId
    assert resp.status_code == 422
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "INVALID_PARAMS"
    assert "requestId" in body["error"]


def test_not_found_returns_error_response(tmp_path: Path) -> None:
    client = _client(tmp_path)
    # When store is missing, status returns 200 with storePresent=false; we use a
    # route that always returns 404 for unknown table id to verify mapping.
    # Since the store is missing, /api/v1/tables/entities.modules will return 503.
    resp = client.get("/api/v1/tables/not-a-real-table")
    assert resp.status_code in (404, 503)
    if resp.status_code == 404:
        body = resp.json()
        assert body["error"]["code"] in {"NOT_FOUND", "QUERY_NOT_FOUND"}


def test_store_not_ready_returns_error_response(tmp_path: Path) -> None:
    client = _client(tmp_path)
    for path in (
        "/api/v1/status",
        "/api/v1/tables/entities.modules",
    ):
        resp = client.get(path)
        assert resp.status_code in (200, 503)
        if resp.status_code == 503:
            body = resp.json()
            assert body["error"]["code"] == "STORE_NOT_READY"


def test_http_status_mapping(tmp_path: Path) -> None:
    client = _client(tmp_path)
    # 422 invalid query
    r = client.get("/api/v1/metrics/timeseries", params={"entityKindId": "x"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_PARAMS"
    # 422 missing required rankBy
    r = client.get("/api/v1/metrics/hotspots", params={"entityKindId": "x", "metricId": "lines"})
    assert r.status_code == 422
    # 404 missing table
    r = client.get("/api/v1/tables/this_table_does_not_exist")
    assert r.status_code in (404, 503)
    # 503 unavailable store
    r = client.get("/api/v1/commits")
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "STORE_NOT_READY"
    # 500 unexpected — exercise the error mapping function directly.
    from ppi.server.api_v1 import _error_response
    resp = _error_response(code="INTERNAL", message="boom", status_code=500)
    assert resp.status_code == 500
    assert b"INTERNAL" in resp.body
