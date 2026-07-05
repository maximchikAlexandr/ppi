from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import msgspec

from ppi.runtime.paths import (
    analysis_dir_for_repo,
    project_id_from_repo,
)


class WorkspaceRegistration(msgspec.Struct):
    workspace_id: str
    project_path: str
    analysis_path: str
    profile: str
    display_name: str
    created_at: str
    updated_at: str


def registry_path() -> Path:
    override = os.environ.get("PPI_WORKSPACE_REGISTRY")
    if override:
        return Path(override)
    return Path.home() / ".local" / "share" / "ppi" / "workspaces.json"


def load_registry() -> dict[str, WorkspaceRegistration]:
    path = registry_path()
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        return msgspec.json.decode(raw, type=dict[str, WorkspaceRegistration])
    except (msgspec.DecodeError, msgspec.ValidationError, ValueError):
        return {}


def save_registry(records: dict[str, WorkspaceRegistration]) -> None:
    path = registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(msgspec.json.encode(records))


def register_or_update_from_repo(
    repo: Path,
    analysis_dir: Path | None = None,
    profile: str = "odoo",
) -> WorkspaceRegistration:
    workspace_id = project_id_from_repo(repo)
    records = load_registry()
    now = datetime.now(UTC).isoformat()
    analysis = analysis_dir or analysis_dir_for_repo(repo)
    display_name = repo.name
    created = records[workspace_id].created_at if workspace_id in records else now
    records[workspace_id] = WorkspaceRegistration(
        workspace_id=workspace_id,
        project_path=str(repo.resolve()),
        analysis_path=str(analysis),
        profile=profile,
        display_name=display_name,
        created_at=created,
        updated_at=now,
    )
    save_registry(records)
    return records[workspace_id]


def get_workspace(workspace_id: str) -> WorkspaceRegistration | None:
    return load_registry().get(workspace_id)



