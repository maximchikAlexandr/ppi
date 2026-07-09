"""Public /api/v1 responses must expose camelCase field names."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ppi.server.app import create_app
from ppi.server.v1_schemas import CamelModel


def test_camel_alias_serializes_snake_case_field() -> None:
    class M(CamelModel):
        project_id: str | None = None
        commit_order: int = 0

    out = M(project_id="abc", commit_order=7).model_dump(by_alias=True)
    assert out == {"projectId": "abc", "commitOrder": 7}


def test_status_response_uses_camel_case(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    body = client.get("/api/v1/status").json()
    assert set(body.keys()) == {
        "projectId", "branch", "storePresent", "writerActive",
        "commitCount", "apiStatus",
    }


def test_ui_config_uses_camel_case(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    body = client.get("/api/v1/ui/config").json()
    assert "schemaVersion" in body
    assert "metrics" in body
    assert "lineCategories" in body
    assert "graphLenses" in body


def test_error_response_uses_camel_case(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    # Pass all required query params so the handler body runs and the
    # 503 (store not ready) check fires before any Query 422.
    resp = client.get(
        "/api/v1/metrics/timeseries",
        params={"entityKindId": "python.module", "metricId": "lines", "aggregation": "mean"},
    )
    assert resp.status_code == 503
    body = resp.json()
    assert "error" in body
    err = body["error"]
    assert set(err.keys()) >= {"code", "message", "requestId"}
