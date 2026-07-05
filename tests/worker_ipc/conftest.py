from pathlib import Path

import pytest

from ppi.runtime.paths import analysis_dir_for_repo, project_id_from_repo


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    (repo / ".git").mkdir()
    return repo


@pytest.fixture
def ws_id(tmp_repo: Path) -> str:
    return project_id_from_repo(tmp_repo)


@pytest.fixture
def integration_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tmp_repo: Path) -> dict:
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("PPI_WORKSPACE_REGISTRY", str(tmp_path / "workspaces.json"))
    return {
        "repo": tmp_repo,
        "analysis_dir": analysis_dir_for_repo(tmp_repo),
    }
