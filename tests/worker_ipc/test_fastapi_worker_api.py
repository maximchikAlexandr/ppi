"""Tests for FastAPI worker API endpoints (T112, T113, T114)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from ppi.server.app import create_app


@pytest.fixture
def fake_client() -> AsyncMock:
    client = AsyncMock()
    client.health = AsyncMock(return_value={
        "worker_id": "w-1",
        "workspace_id": "ws-1",
        "state": "idle",
        "protocol_version": "1.0",
        "started_at": "2026-01-01T00:00:00Z",
    })
    client.workspace_info = AsyncMock(return_value={
        "workspace_id": "ws-1",
        "project_path": "/test",
        "analysis_path": "/test/analysis",
        "profile": "odoo",
        "display_name": "test",
    })
    client.analysis_status = AsyncMock(return_value={
        "state": "not_started",
        "current_run_id": None,
        "last_run_id": None,
        "progress_percent": None,
        "message": "No analysis run yet",
    })
    client.analysis_start = AsyncMock(return_value={
        "run_id": "run-1",
        "accepted": True,
        "state": "running",
        "message": "Analysis started",
    })
    client.query_execute = AsyncMock(return_value={
        "columns": ["name"], "rows": [{"name": "test"}],
        "row_count": 1, "truncated": False,
    })
    client.close = AsyncMock()
    return client


@pytest.fixture
def app(fake_client: AsyncMock, tmp_path: Path) -> TestClient:
    app = create_app(
        store_file=tmp_path / "store.duckdb",
        lock_file=tmp_path / "writer.lock",
        worker_client=fake_client,
    )
    return TestClient(app)


def test_worker_health_endpoint(app: TestClient) -> None:
    resp = app.get("/api/worker/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["worker_id"] == "w-1"
    assert data["state"] == "idle"


def test_worker_workspace_endpoint(app: TestClient) -> None:
    resp = app.get("/api/worker/workspace")
    assert resp.status_code == 200
    data = resp.json()
    assert data["workspace_id"] == "ws-1"


def test_worker_analysis_status_endpoint(app: TestClient) -> None:
    resp = app.get("/api/worker/analysis/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "not_started"


def test_worker_analysis_start_endpoint(app: TestClient) -> None:
    resp = app.post("/api/worker/analysis/start", json={"mode": "incremental"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "running"
    assert data["run_id"] == "run-1"


def test_worker_analysis_start_already_running(app: TestClient, fake_client: AsyncMock) -> None:
    fake_client.analysis_start = AsyncMock(return_value={
        "run_id": "run-1", "accepted": True,
        "state": "already_running", "message": "Already running",
    })
    resp = app.post("/api/worker/analysis/start", json={"mode": "incremental"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "already_running"


def test_worker_query_endpoint(app: TestClient) -> None:
    resp = app.post("/api/worker/query", json={
        "query_name": "project/info", "parameters": {},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["row_count"] == 1


def test_worker_error_http_conversion(app: TestClient, fake_client: AsyncMock) -> None:
    from ppi.worker_ipc.client import WorkerClientError
    from ppi.worker_ipc.protocol import WorkerError as WorkerErrorStruct
    fake_client.health.side_effect = WorkerClientError(WorkerErrorStruct(
        code="WORKER_BUSY", message="Busy", details={"state": "running"},
    ))
    resp = app.get("/api/worker/health")
    assert resp.status_code == 409
    detail = resp.json()
    assert detail.get("detail", {}).get("code") == "WORKER_BUSY"
