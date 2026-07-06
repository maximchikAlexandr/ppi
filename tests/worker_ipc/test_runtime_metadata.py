from pathlib import Path

import pytest

from ppi.worker_ipc.runtime_metadata import (
    RuntimeMetadata,
    mark_stale,
    read_metadata,
    remove_metadata,
    write_metadata,
)


@pytest.fixture
def meta() -> RuntimeMetadata:
    return RuntimeMetadata(
        workspace_id="ws-1",
        worker_id="w-1",
        pid=12345,
        endpoint="unix:///tmp/sock",
        state="idle",
        started_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:05Z",
        last_heartbeat_at="2026-01-01T00:00:05Z",
    )


def test_write_and_read(tmp_path: Path, meta: RuntimeMetadata) -> None:
    path = tmp_path / "worker.json"
    write_metadata(path, meta)
    assert path.is_file()
    loaded = read_metadata(path)
    assert loaded is not None
    assert loaded.workspace_id == "ws-1"
    assert loaded.worker_id == "w-1"
    assert loaded.state == "idle"
    assert loaded.pid == 12345


def test_read_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "nonexistent.json"
    assert read_metadata(path) is None


def test_corrupted_json(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.json"
    path.write_text("{bad json}", encoding="utf-8")
    assert read_metadata(path) is None


def test_mark_stale(tmp_path: Path, meta: RuntimeMetadata) -> None:
    path = tmp_path / "worker.json"
    write_metadata(path, meta)
    result = mark_stale(path)
    assert result is not None
    assert result.state == "stale"
    loaded = read_metadata(path)
    assert loaded is not None
    assert loaded.state == "stale"


def test_mark_stale_with_reason(tmp_path: Path, meta: RuntimeMetadata) -> None:
    path = tmp_path / "worker.json"
    write_metadata(path, meta)
    result = mark_stale(path, "lock timeout")
    assert result is not None
    assert result.state == "stale"
    assert result.last_error == {"reason": "lock timeout"}


def test_remove_metadata(tmp_path: Path, meta: RuntimeMetadata) -> None:
    path = tmp_path / "worker.json"
    write_metadata(path, meta)
    assert path.is_file()
    remove_metadata(path)
    assert not path.is_file()
    remove_metadata(path)
    assert not path.is_file()


def test_corrupt_renamed(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.json"
    path.write_text("{bad json}", encoding="utf-8")
    assert read_metadata(path) is None
    siblings = [p.name for p in path.parent.iterdir()]
    assert any(s.startswith("corrupt.json.corrupt.") for s in siblings)



