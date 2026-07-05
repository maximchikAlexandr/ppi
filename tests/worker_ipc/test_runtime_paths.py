import os
from pathlib import Path

import pytest

from ppi.worker_ipc.runtime_paths import (
    endpoint_for_workspace,
    metadata_path,
    runtime_dir,
    runtime_root,
    socket_path,
    startup_lock_path,
)


def test_runtime_root_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    root = runtime_root()
    assert root == Path("/run/user/1000/ppi")


def test_runtime_root_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    root = runtime_root()
    uid = os.getuid()
    assert root == Path(f"/tmp/ppi/{uid}")


def test_runtime_dir() -> None:
    assert runtime_dir("test-ws") == runtime_root() / "test-ws"


def test_socket_path() -> None:
    assert socket_path("test-ws") == runtime_dir("test-ws") / "worker.sock"


def test_metadata_path() -> None:
    assert metadata_path("test-ws") == runtime_dir("test-ws") / "worker.json"


def test_startup_lock_path() -> None:
    assert startup_lock_path("test-ws") == runtime_dir("test-ws") / "worker.lock"


def test_endpoint_for_workspace() -> None:
    ws_id = "test-ws"
    ep = endpoint_for_workspace(ws_id)
    assert ep.transport == "unix"
    assert ep.path == str(socket_path(ws_id))
