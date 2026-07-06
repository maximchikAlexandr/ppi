from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import msgspec

from ppi.runtime.paths import (
    analysis_dir_for_repo,
    project_id_from_repo,
)


class WorkspaceRegistration(msgspec.Struct, frozen=True, kw_only=True):
    workspace_id: str
    project_path: str
    analysis_path: str
    profile: str
    display_name: str
    created_at: str
    updated_at: str


class RegistryCorruptedError(Exception):
    """Raised when the registry file exists but cannot be parsed."""


def registry_path() -> Path:
    override = os.environ.get("PPI_WORKSPACE_REGISTRY")
    if override:
        return Path(override)
    return Path.home() / ".local" / "share" / "ppi" / "workspaces.json"


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_bytes(data)
    tmp.replace(path)


def load_registry() -> dict[str, WorkspaceRegistration]:
    path = registry_path()
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        return msgspec.json.decode(raw, type=dict[str, WorkspaceRegistration])
    except (msgspec.DecodeError, msgspec.ValidationError, ValueError) as exc:
        try:
            ts = path.stat().st_mtime
            path.rename(path.with_name(f"workspaces.json.corrupt.{ts}"))
        except OSError:
            pass
        raise RegistryCorruptedError(f"Workspace registry is corrupted: {exc}") from exc


def save_registry(records: dict[str, WorkspaceRegistration]) -> None:
    _atomic_write(registry_path(), msgspec.json.encode(records))


def register_or_update_from_repo(
    repo: Path,
    analysis_dir: Path | None = None,
    profile: str = "odoo",
) -> WorkspaceRegistration:
    workspace_id = project_id_from_repo(repo)
    try:
        records = load_registry()
    except RegistryCorruptedError:
        records = {}
    now = datetime.now(UTC).isoformat()
    analysis = analysis_dir or analysis_dir_for_repo(repo)
    display_name = repo.name
    created = records[workspace_id].created_at if workspace_id in records else now
    new_reg = WorkspaceRegistration(
        workspace_id=workspace_id,
        project_path=str(repo.resolve()),
        analysis_path=str(analysis),
        profile=profile,
        display_name=display_name,
        created_at=created,
        updated_at=now,
    )
    new_records = {**records, workspace_id: new_reg}
    save_registry(new_records)
    return new_reg


def get_workspace(workspace_id: str) -> WorkspaceRegistration | None:
    try:
        return load_registry().get(workspace_id)
    except RegistryCorruptedError:
        return None


def resolve_workspace_from_repo(repo: Path) -> WorkspaceRegistration | None:
    workspace_id = project_id_from_repo(repo)
    return get_workspace(workspace_id)


def list_workspaces() -> list[WorkspaceRegistration]:
    try:
        records = load_registry()
    except RegistryCorruptedError:
        return []
    return sorted(records.values(), key=lambda r: r.workspace_id)



