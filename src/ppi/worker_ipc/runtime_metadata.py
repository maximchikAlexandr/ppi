from __future__ import annotations

from pathlib import Path
from typing import Any

import msgspec
from msgspec import structs as msgspec_structs


class RuntimeMetadata(msgspec.Struct, frozen=True):
    workspace_id: str
    worker_id: str
    pid: int
    endpoint: str
    transport: str = "unix"
    protocol_version: str = "1.0"
    state: str = "starting"
    started_at: str = ""
    updated_at: str = ""
    last_heartbeat_at: str = ""
    last_error: dict[str, Any] | None = None


def read_metadata(path: Path) -> RuntimeMetadata | None:
    if not path.is_file():
        return None
    try:
        return msgspec.json.decode(path.read_bytes(), type=RuntimeMetadata)
    except (msgspec.ValidationError, msgspec.DecodeError, ValueError):
        return None


def write_metadata(path: Path, meta: RuntimeMetadata) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(msgspec.json.encode(meta))


def mark_stale(path: Path) -> RuntimeMetadata | None:
    meta = read_metadata(path)
    if meta is not None:
        meta = msgspec_structs.replace(meta, state="stale")
        write_metadata(path, meta)
    return meta



