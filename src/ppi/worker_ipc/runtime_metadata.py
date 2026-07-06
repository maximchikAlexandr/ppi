from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import msgspec
from msgspec import structs as msgspec_structs


class RuntimeMetadata(msgspec.Struct, frozen=True, kw_only=True):
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


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_bytes(data)
    tmp.replace(path)


def read_metadata(path: Path) -> RuntimeMetadata | None:
    if not path.is_file():
        return None
    try:
        return msgspec.json.decode(path.read_bytes(), type=RuntimeMetadata)
    except (msgspec.ValidationError, msgspec.DecodeError, ValueError):
        try:
            ts = path.stat().st_mtime
            path.rename(path.with_name(f"{path.name}.corrupt.{int(ts)}"))
        except OSError:
            pass
        return None


def write_metadata(path: Path, meta: RuntimeMetadata) -> None:
    _atomic_write(path, msgspec.json.encode(meta))


def mark_stale(path: Path, reason: str = "") -> RuntimeMetadata | None:
    meta = read_metadata(path)
    if meta is not None:
        meta = msgspec_structs.replace(
            meta,
            state="stale",
            last_error={"reason": reason} if reason else meta.last_error,
        )
        write_metadata(path, meta)
    return meta


def remove_metadata(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass



