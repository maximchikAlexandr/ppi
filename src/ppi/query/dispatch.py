"""Shared query dispatcher for dashboard read surface.

Routes through Ibis pipeline — returns ``Result``; adapters convert to errors.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from ppi.core.errors import DomainError, ErrorCode, ErrorCategory
from ppi.core.result import Error, Ok, Result
from ppi.query import _handlers as h
from ppi.query import schemas
from ppi.query._params import QueryError
from ppi.query.contracts import QueryParams
from ppi.storage import schema


class QueryMethod(StrEnum):
    COMMITS = "commits"
    METRICS_TIMESERIES = "metrics/timeseries"
    HOTSPOTS = "hotspots"
    GRAPH = "graph"
    UI_CONFIG = "ui/config"
    SNAPSHOT_TABLE_MODULES = "snapshot/table/modules"
    SNAPSHOT_TABLE_FILES = "snapshot/table/files"
    SNAPSHOT_RELATIONS = "snapshot/relations"
    PROJECT_INFO = "project/info"


_METHOD_TABLE: dict[QueryMethod, Any] = {
    QueryMethod.COMMITS: h.commits,
    QueryMethod.METRICS_TIMESERIES: h.metrics_timeseries,
    QueryMethod.HOTSPOTS: h.hotspots,
    QueryMethod.GRAPH: h.graph,
    QueryMethod.UI_CONFIG: h.ui_config,
    QueryMethod.SNAPSHOT_TABLE_MODULES: h.snapshot_table_modules,
    QueryMethod.SNAPSHOT_TABLE_FILES: h.snapshot_table_files,
    QueryMethod.SNAPSHOT_RELATIONS: h.snapshot_relations,
}


def build_project_info(
    *,
    store_file: Path | None,
    store_present: bool,
    writer_active: bool,
    schema_error: schema.SchemaIncompatibleError | None = None,
) -> schemas.ProjectInfoResponse:
    if schema_error is not None:
        return schemas.ProjectInfoResponse(
            project_id=None, branch=None, commit_count=0,
            schema_version=schema_error.stored, store_present=store_present,
        )
    if store_file is None or not store_present:
        return schemas.ProjectInfoResponse(
            project_id=None, branch=None, commit_count=0,
            schema_version=schema.SCHEMA_VERSION, store_present=store_present,
        )
    from ppi.query.pipeline import run_query
    result = run_query(store_file, QueryParams(metric="project-info"))
    if result.is_ok() and result.ok:
        rows = result.ok
        row = rows[0] if rows else {}
        return schemas.ProjectInfoResponse(
            project_id=row.get("project_id"), branch=row.get("branch"),
            commit_count=row.get("commit_count", 0), schema_version=schema.SCHEMA_VERSION, store_present=store_present,
        )
    return schemas.ProjectInfoResponse(
        project_id=None, branch=None, commit_count=0,
        schema_version=schema.SCHEMA_VERSION, store_present=store_present,
    )


def dispatch(
    store_file: Path | None,
    method: str,
    params: dict,
    *,
    writer_active: bool = False,
    store_present: bool = True,
    schema_error: schema.SchemaIncompatibleError | None = None,
) -> Result[Any, DomainError]:
    try:
        typed = QueryMethod(method)
    except ValueError:
        return Error(DomainError(
            ErrorCode.QUERY_ERROR, ErrorCategory.QUERY,
            f"unknown method: {method}",
            details=(("http_status", 404), ("code", "METHOD_NOT_FOUND")),
        ))

    if typed == QueryMethod.PROJECT_INFO:
        return Ok(build_project_info(
            store_file=store_file, store_present=store_present,
            writer_active=writer_active, schema_error=schema_error,
        ))

    if writer_active:
        return Error(DomainError(
            ErrorCode.LOCK_ERROR, ErrorCategory.LOCK,
            "analysis in progress",
            details=(("http_status", 409), ("code", "LOCKED")),
        ))
    if schema_error is not None:
        return Error(DomainError(
            ErrorCode.SCHEMA_ERROR, ErrorCategory.SCHEMA,
            str(schema_error),
            details=(("http_status", 503), ("code", "SCHEMA_INCOMPATIBLE")),
        ))
    if store_file is None or not store_present:
        return Error(DomainError(
            ErrorCode.STORAGE_ERROR, ErrorCategory.STORAGE,
            "store not found",
            details=(("http_status", 503), ("code", "STORE_NOT_FOUND")),
        ))

    handler = _METHOD_TABLE[typed]
    try:
        return handler(store_file, params)
    except QueryError as exc:
        return Error(DomainError(
            ErrorCode.QUERY_ERROR, ErrorCategory.QUERY,
            exc.message,
            details=(("http_status", exc.http_status), ("code", exc.code)),
        ))
    except Exception as exc:
        return Error(DomainError(
            ErrorCode.UNEXPECTED_ERROR, ErrorCategory.RUNTIME,
            str(exc),
            details=(("http_status", 500), ("code", "INTERNAL")),
        ))
