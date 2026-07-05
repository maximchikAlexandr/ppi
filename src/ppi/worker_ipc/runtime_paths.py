from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Endpoint:
    transport: str
    path: str

    def uri(self) -> str:
        return f"{self.transport}://{self.path}"


def runtime_root() -> Path:
    xdg = os.environ.get("XDG_RUNTIME_DIR")
    if xdg:
        return Path(xdg) / "ppi"
    uid = os.getuid()
    return Path(f"/tmp/ppi/{uid}")


def runtime_dir(workspace_id: str) -> Path:
    return runtime_root() / workspace_id


def socket_path(workspace_id: str) -> Path:
    return runtime_dir(workspace_id) / "worker.sock"


def metadata_path(workspace_id: str) -> Path:
    return runtime_dir(workspace_id) / "worker.json"


def startup_lock_path(workspace_id: str) -> Path:
    return runtime_dir(workspace_id) / "worker.lock"


def endpoint_for_workspace(workspace_id: str) -> Endpoint:
    return Endpoint(transport="unix", path=str(socket_path(workspace_id)))
