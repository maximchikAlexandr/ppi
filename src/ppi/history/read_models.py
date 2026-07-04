"""History read-model queries routed through Ibis builders and execution boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ppi.core.errors import DomainError
from ppi.core.result import Error, Ok, Result
from ppi.storage.ibis_backend import connect_ibis, disconnect_backend, execute_expr, load_table
from ppi.storage.ibis_queries import select_commit_timeline, select_project


def query_project_info(store_file: Path) -> Result[dict[str, Any], DomainError]:
    backend_result = connect_ibis(store_file)
    if backend_result.is_error():
        return Error(backend_result.error)
    backend = backend_result.ok
    try:
        project_table = load_table(backend, "project")
        if project_table.is_error():
            return Error(project_table.error)
        expr = select_project(project_table.ok)
        result = execute_expr(backend, expr)
        if result.is_error():
            return Error(result.error)
        rows = result.ok
        info = {
            "project_id": rows[0].get("project_id") if rows else None,
            "branch": rows[0].get("branch") if rows else None,
            "commit_count": 0,
        }
        return Ok(info)
    finally:
        disconnect_backend(backend)


def query_commits(store_file: Path) -> Result[list[dict[str, Any]], DomainError]:
    backend_result = connect_ibis(store_file)
    if backend_result.is_error():
        return Error(backend_result.error)
    backend = backend_result.ok
    try:
        commit_table = load_table(backend, "commit")
        if commit_table.is_error():
            return Error(commit_table.error)
        expr = select_commit_timeline(commit_table.ok)
        result = execute_expr(backend, expr)
        if result.is_error():
            return Error(result.error)
        return Ok(result.ok)
    finally:
        disconnect_backend(backend)
