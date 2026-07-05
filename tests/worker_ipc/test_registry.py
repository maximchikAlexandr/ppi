from pathlib import Path

import pytest

from ppi.worker_ipc.registry import (
    WorkspaceRegistration,
    get_workspace,
    load_registry,
    registry_path,
    save_registry,
)


def _make_reg(workspace_id: str = "ws-1") -> WorkspaceRegistration:
    return WorkspaceRegistration(
        workspace_id=workspace_id,
        project_path="/tmp/proj",
        analysis_path="/tmp/analysis",
        profile="odoo",
        display_name="proj",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )


@pytest.fixture
def reg_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    reg_path = tmp_path / "test-workspaces.json"
    monkeypatch.setenv("PPI_WORKSPACE_REGISTRY", str(reg_path))
    return reg_path


def test_registry_path_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    reg_path = tmp_path / "test-workspaces.json"
    monkeypatch.setenv("PPI_WORKSPACE_REGISTRY", str(reg_path))
    assert registry_path() == reg_path


def test_load_save_roundtrip(reg_env: Path) -> None:
    orig = {"ws-1": _make_reg("ws-1")}
    save_registry(orig)
    loaded = load_registry()
    assert "ws-1" in loaded
    assert loaded["ws-1"].workspace_id == "ws-1"


def test_get_workspace(reg_env: Path) -> None:
    reg = _make_reg("ws-1")
    save_registry({"ws-1": reg})
    result = get_workspace("ws-1")
    assert result is not None
    assert result.workspace_id == "ws-1"
    assert get_workspace("nonexistent") is None



def test_empty_registry(reg_env: Path) -> None:
    save_registry({})
    records = load_registry()
    assert records == {}


def test_no_registry_file(reg_env: Path) -> None:
    records = load_registry()
    assert records == {}
