"""Public ``/api/v1`` router.

Thin FastAPI glue: extract params, resolve commit, call one projection
in ``ppi.query.projections`` (the functional core), return. No row
shaping, no camelCase string literals — the CamelModel alias generator
in ``v1_schemas.py`` is the sole naming authority.

ponytail: entity-kind -> query-metric dispatch (L246/496/552) maps a
public entity-kind id to an internal query metric name; generalize
when a 3rd kind is added.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ppi.contracts.errors import ErrorCode, ERRORS, http_status_for
from ppi.query import dispatch
from ppi.query import metric_catalog
from ppi.query import pipeline as query_pipeline
from ppi.query.contracts import QueryParams
from ppi.query.profile_kinds import LEVEL_FILE, is_file_kind
from ppi.query.projections import (
    TABLE_FILES_ID,
    TABLE_MODULES_ID,
    TABLE_RELATIONS_ID,
    build_commits_projection,
    build_entity_projection,
    build_graph_projection,
    build_hotspots_projection,
    build_status_projection,
    build_table_files_projection,
    build_table_modules_projection,
    build_table_relations_projection,
    build_tables_index_projection,
    build_timeseries_projection,
    build_ui_config_projection,
)
from ppi.runtime import lock as project_lock
from ppi.server.v1_schemas import (
    GraphV1Response,
    ListCommitsV1Response,
    ListEntitiesV1Response,
    ListTablesV1Response,
    MetricHotspotsV1Response,
    MetricTimeseriesV1Response,
    StatusV1Response,
    TableV1Response,
    UiConfigV1Response,
)

_LOG = logging.getLogger(__name__)

_TABLE_MODULES_ALIASES: frozenset[str] = frozenset({TABLE_MODULES_ID, "modules"})
_TABLE_FILES_ALIASES: frozenset[str] = frozenset({TABLE_FILES_ID, "files"})
_TABLE_RELATIONS_ALIASES: frozenset[str] = frozenset({TABLE_RELATIONS_ID, "relations"})

router = APIRouter()


def _error_response(
    *, code: str, message: str, status_code: int, details: Any | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "requestId": request_id or str(uuid.uuid4()),
        }
    }
    return JSONResponse(status_code=status_code, content=body)


def _contract_error(code: ErrorCode, detail: str, details: Any | None = None) -> JSONResponse:
    return _error_response(
        code=code.value,
        message=ERRORS[code].default_message,
        status_code=http_status_for(code) or 500,
        details=details,
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _http_exc(request: Request, exc: HTTPException):  # type: ignore[unused-ignore]
        if exc.status_code == 422:
            return _contract_error(ErrorCode.VALIDATION_ERROR, str(exc.detail))
        if exc.status_code == 404:
            return _contract_error(ErrorCode.NOT_FOUND, str(exc.detail))
        return _contract_error(ErrorCode.INTERNAL_ERROR, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request: Request, exc: RequestValidationError):  # type: ignore[unused-ignore]
        return _contract_error(
            ErrorCode.VALIDATION_ERROR,
            "request validation failed",
            details=exc.errors(),
        )


def _store_file(request: Request):
    return request.app.state.store_file


def _store_present(request: Request) -> bool:
    return _store_file(request).is_file()


def _writer_active(request: Request) -> bool:
    return project_lock.is_locked(request.app.state.lock_file)


def _require_ok(result: Any, *, code: ErrorCode, detail: str) -> Any:
    if not result.is_ok() or result.ok is None:
        raise _contract_error(code, detail)
    return result.ok


@router.get(
    "/status",
    response_model=StatusV1Response,
    operation_id="getStatusV1",
    tags=["status"],
    summary="Project status",
)
def get_status_v1(request: Request):
    sf = _store_file(request)
    present = _store_present(request)
    writer = _writer_active(request)
    project_id = None
    branch = None
    commit_count = 0
    if present and not writer:
        try:
            info = dispatch.build_project_info(
                store_file=sf, store_present=present,
                writer_active=writer, schema_error=None,
            )
            project_id = info.project_id
            branch = info.branch
            commit_count = info.commit_count
        except Exception as exc:
            _LOG.warning("build_project_info failed: %s", exc)
    return build_status_projection(
        project_id=project_id, branch=branch,
        commit_count=commit_count, store_present=present,
        writer_active=writer,
    )


@router.get(
    "/ui/config",
    response_model=UiConfigV1Response,
    operation_id="getUiConfigV1",
    tags=["ui"],
    summary="Generic UI configuration",
)
def get_ui_config_v1(request: Request):
    return build_ui_config_projection()


@router.get(
    "/commits",
    response_model=ListCommitsV1Response,
    operation_id="listCommitsV1",
    tags=["commits"],
    summary="List commits ordered by commit order",
)
def list_commits_v1(request: Request):
    sf = _store_file(request)
    if not _store_present(request):
        raise _contract_error(ErrorCode.STORE_NOT_READY, "store not ready")
    rows = _require_ok(
        query_pipeline.run_query(sf, QueryParams(metric="commits")),
        code=ErrorCode.STORE_NOT_READY, detail="commits query failed",
    )
    return build_commits_projection(rows)


@router.get(
    "/entities",
    response_model=ListEntitiesV1Response,
    operation_id="listEntitiesV1",
    tags=["entities"],
    summary="List entities of one kind at a commit",
)
def list_entities_v1(
    request: Request,
    entity_kind_id: str = Query(..., min_length=1, alias="entityKindId"),
    commit_id: str | None = Query(None, alias="commitId"),
    limit: int = Query(5000, ge=1, le=10000),
):
    sf = _store_file(request)
    if not _store_present(request):
        raise _contract_error(ErrorCode.STORE_NOT_READY, "store not ready")
    commit = query_pipeline.resolve_commit(sf, commit_id)
    if commit is None:
        raise _contract_error(ErrorCode.NOT_FOUND, "commit not found")
    metric = query_pipeline.metric_for_entity_kind(entity_kind_id)
    rows = _require_ok(
        query_pipeline.run_query(
            sf, QueryParams(metric=metric, commit_hash=commit.get("commit_hash"), limit=limit),
        ),
        code=ErrorCode.NOT_FOUND, detail="no entities",
    )
    return build_entity_projection(
        entity_kind_id=entity_kind_id,
        commit_id=commit.get("commit_hash"),
        rows=rows,
    )


@router.get(
    "/graph",
    response_model=GraphV1Response,
    operation_id="getGraphV1",
    tags=["graph"],
    summary="Generic graph projection",
)
def get_graph_v1(
    request: Request,
    lens_id: str = Query(..., min_length=1, alias="lensId"),
    commit_id: str | None = Query(None, alias="commitId"),
    include_zero_weight: bool = Query(False, alias="includeZeroWeight"),
):
    sf = _store_file(request)
    if not _store_present(request):
        raise _contract_error(ErrorCode.STORE_NOT_READY, "store not ready")
    commit = query_pipeline.resolve_commit(sf, commit_id)
    if commit is None:
        raise _contract_error(ErrorCode.NOT_FOUND, "commit not found")
    data = _require_ok(
        query_pipeline.run_query(
            sf,
            QueryParams(
                metric="graph",
                commit_hash=commit.get("commit_hash"),
                include_zero_score=include_zero_weight,
            ),
        ),
        code=ErrorCode.NOT_FOUND, detail="graph not available",
    )
    return build_graph_projection(
        commit_id=commit.get("commit_hash"),
        lens_id=lens_id, data=data,
    )


@router.get(
    "/tables",
    response_model=ListTablesV1Response,
    operation_id="listTablesV1",
    tags=["tables"],
    summary="List generic table definitions",
)
def list_tables_v1(request: Request):
    return build_tables_index_projection()


@router.get(
    "/tables/{tableId}",
    response_model=TableV1Response,
    operation_id="getTableV1",
    tags=["tables"],
    summary="Generic table projection",
)
def get_table_v1(
    request: Request,
    table_id: str = Path(..., alias="tableId"),
    commit_id: str | None = Query(None, alias="commitId"),
    parent_entity_id: str | None = Query(None, alias="parentEntityId"),
    limit: int = Query(500, ge=1, le=5000),
):
    sf = _store_file(request)
    if not _store_present(request):
        raise _contract_error(ErrorCode.STORE_NOT_READY, "store not ready")
    commit = query_pipeline.resolve_commit(sf, commit_id)
    if commit is None:
        raise _contract_error(ErrorCode.NOT_FOUND, "commit not found")
    hash_ = commit.get("commit_hash")

    if table_id in _TABLE_MODULES_ALIASES:
        data = _require_ok(
            query_pipeline.run_query(sf, QueryParams(metric="snapshot-table-modules", commit_hash=hash_)),
            code=ErrorCode.NOT_FOUND, detail="no data",
        )
        return build_table_modules_projection(commit_id=hash_, data=data)

    if table_id in _TABLE_FILES_ALIASES:
        data = _require_ok(
            query_pipeline.run_query(
                sf,
                QueryParams(metric="snapshot-table-files", commit_hash=hash_,
                            module_name=parent_entity_id),
            ),
            code=ErrorCode.NOT_FOUND, detail="no data",
        )
        return build_table_files_projection(
            commit_id=hash_, parent_entity_id=parent_entity_id, data=data,
        )

    if table_id in _TABLE_RELATIONS_ALIASES:
        rows_in = _require_ok(
            query_pipeline.run_query(sf, QueryParams(metric="snapshot-relations", commit_hash=hash_)),
            code=ErrorCode.NOT_FOUND, detail="no data",
        )
        return build_table_relations_projection(commit_id=hash_, rows_in=rows_in)

    raise _contract_error(ErrorCode.NOT_FOUND, f"unknown table: {table_id}")


@router.get(
    "/metrics/timeseries",
    response_model=MetricTimeseriesV1Response,
    operation_id="getMetricTimeseriesV1",
    tags=["metrics"],
    summary="Generic metric timeseries",
)
def get_metric_timeseries_v1(
    request: Request,
    entity_kind_id: str = Query(..., min_length=1, alias="entityKindId"),
    metric_id: str = Query(..., min_length=1, alias="metricId"),
    aggregation: str = Query("mean", min_length=1),
    target_id: str | None = Query(None, alias="targetId"),
    commit_id: str | None = Query(None, alias="commitId"),
):
    sf = _store_file(request)
    if not _store_present(request):
        raise _contract_error(ErrorCode.STORE_NOT_READY, "store not ready")
    commit = query_pipeline.resolve_commit(sf, commit_id)
    if commit is None:
        raise _contract_error(ErrorCode.NOT_FOUND, "commit not found")
    try:
        metric_catalog.validate_metric_id(metric_id)
    except ValueError as exc:
        raise _contract_error(ErrorCode.VALIDATION_ERROR, str(exc)) from exc
    level = LEVEL_FILE if is_file_kind(entity_kind_id) else "module"
    if level is LEVEL_FILE:
        module, _, path = (target_id or "").partition("/")
        if not module or not path:
            raise _contract_error(
                ErrorCode.VALIDATION_ERROR,
                "targetId must be module/relative/path for file kind",
            )
        result = query_pipeline.run_query(
            sf,
            QueryParams(metric="file-timeseries", commit_hash=commit.get("commit_hash"),
                        module_name=module, file_path=path,
                        metric_id=metric_id, agg=aggregation),
        )
    else:
        result = query_pipeline.run_query(
            sf,
            QueryParams(metric="module-timeseries", commit_hash=commit.get("commit_hash"),
                        module_name=target_id or "", metric_id=metric_id, agg=aggregation),
        )
    points = _require_ok(result, code=ErrorCode.NOT_FOUND, detail="no data")
    return build_timeseries_projection(
        entity_kind_id=entity_kind_id, metric_id=metric_id,
        aggregation=aggregation, target_id=target_id, level=level,
        points=points,
    )


@router.get(
    "/metrics/hotspots",
    response_model=MetricHotspotsV1Response,
    operation_id="getMetricHotspotsV1",
    tags=["metrics"],
    summary="Generic metric hotspots",
)
def get_metric_hotspots_v1(
    request: Request,
    entity_kind_id: str = Query(..., min_length=1, alias="entityKindId"),
    metric_id: str = Query(..., min_length=1, alias="metricId"),
    aggregation: str = Query("mean", min_length=1),
    rank_by: str = Query(..., pattern="^(value|growth)$", alias="rankBy"),
    limit: int = Query(20, ge=1, le=100),
):
    sf = _store_file(request)
    if not _store_present(request):
        raise _contract_error(ErrorCode.STORE_NOT_READY, "store not ready")
    level = LEVEL_FILE if is_file_kind(entity_kind_id) else "module"
    try:
        metric_catalog.validate_metric_id(metric_id, level=level)
    except ValueError as exc:
        raise _contract_error(ErrorCode.VALIDATION_ERROR, str(exc)) from exc
    items_raw = _require_ok(
        query_pipeline.run_query(
            sf,
            QueryParams(metric="hotspots", metric_id=metric_id,
                        agg=aggregation, level=level, limit=limit),
        ),
        code=ErrorCode.NOT_FOUND, detail="no data",
    )
    return build_hotspots_projection(
        entity_kind_id=entity_kind_id, metric_id=metric_id,
        aggregation=aggregation, rank_by=rank_by, items_raw=items_raw,
    )


__all__ = ["router", "install_error_handlers"]
