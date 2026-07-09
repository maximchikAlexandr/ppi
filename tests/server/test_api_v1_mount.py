"""Mount test: /api/v1 routes coexist with legacy /api routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ppi.server.app import create_app


def test_api_v1_mount_keeps_legacy(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    # legacy /api/commits stays
    legacy = client.get("/api/commits")
    assert legacy.status_code in (200, 503, 422)

    # /api/v1/status is mounted and returns camelCase fields even with no store
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "projectId" in body
    assert "branch" in body
    assert "storePresent" in body
    assert "writerActive" in body
    assert "commitCount" in body
    assert "apiStatus" in body
