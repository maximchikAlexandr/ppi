"""Shared, FastAPI-free query dispatcher for the dashboard read surface.

Both ``ppi serve`` (HTTP) and ``ppi rpc`` (stdio JSON-RPC) route dashboard reads
through this module so behavior is identical (Spec FR-008/SC-003). The dispatcher
returns pydantic ``schemas`` model instances (or plain dicts/lists) so both
transports serialize the same JSON. HTTP-specific concerns (status codes,
opening the store) live in the callers; this module owns the writer-lock check,
schema-error normalization, and raises ``QueryError`` for invalid input or
missing data.

Endpoint handlers live in :mod:`ppi.query._handlers`; this module owns only the
method table, the router, ``build_status``, and error normalization. Method
names are typed via :class:`QueryMethod` (PPI-045) and dispatched via a typed
table; string methods remain only at the HTTP/RPC decoder boundary.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from ppi.query import _handlers as h
from ppi.query import schemas
from ppi.query._params import QueryError
from ppi.query.errors import QueryErrorCode, raise_query_failure
from ppi.storage import schema
from ppi.storage.queries import QueryNotFoundError, StoreReader


class QueryMethod(StrEnum):
    """Typed query method names (PPI-045).

    String values stay stable for the HTTP/RPC boundary; inside the dispatcher
    routing uses the typed enum.
    """

    COMMITS = "commits"
    CATALOG = "catalog"
    METRICS_TIMESERIES = "metrics/timeseries"
    HOTSPOTS = "hotspots"
    STRUCTURE_TIMESERIES = "structure/timeseries"
    EDGES = "edges"
    SNAPSHOT_MODULES = "snapshot/modules"
    SNAPSHOT_FILES = "snapshot/files"
    SNAPSHOT_MODULE = "snapshot/module"
    SNAPSHOT_FILE = "snapshot/file"
    GRAPH = "graph"
    EDGE_POINTS = "edge-points"
    EDGE_POINTS_BATCH = "edge-points/batch"
    EDGE_EVIDENCE = "edge-evidence"
    MODELS = "models"
    DEPENDS = "depends"
    FAILURES = "failures"
    EDGE_KIND_TIMESERIES = "edge-kinds/timeseries"
    RELATIONS_DIFF = "relations/diff"
    STATUS = "status"


DATA_METHODS = {
    QueryMethod.COMMITS,
    QueryMethod.CATALOG,
    QueryMethod.METRICS_TIMESERIES,
    QueryMethod.HOTSPOTS,
    QueryMethod.STRUCTURE_TIMESERIES,
    QueryMethod.EDGES,
    QueryMethod.SNAPSHOT_MODULES,
    QueryMethod.SNAPSHOT_FILES,
    QueryMethod.SNAPSHOT_MODULE,
    QueryMethod.SNAPSHOT_FILE,
    QueryMethod.GRAPH,
    QueryMethod.EDGE_POINTS,
    QueryMethod.EDGE_POINTS_BATCH,
    QueryMethod.EDGE_EVIDENCE,
    QueryMethod.MODELS,
    QueryMethod.DEPENDS,
    QueryMethod.FAILURES,
    QueryMethod.EDGE_KIND_TIMESERIES,
    QueryMethod.RELATIONS_DIFF,
}

ALL_METHODS = DATA_METHODS | {QueryMethod.STATUS}

# Typed handler table: QueryMethod -> handler callable (no string keys).
_METHOD_TABLE: dict[QueryMethod, Any] = {
    QueryMethod.COMMITS: h.commits,
    QueryMethod.CATALOG: h.catalog,
    QueryMethod.METRICS_TIMESERIES: h.metrics_timeseries,
    QueryMethod.HOTSPOTS: h.hotspots,
    QueryMethod.STRUCTURE_TIMESERIES: h.structure_timeseries,
    QueryMethod.EDGES: h.edges,
    QueryMethod.SNAPSHOT_MODULES: h.snapshot_modules,
    QueryMethod.SNAPSHOT_FILES: h.snapshot_files,
    QueryMethod.SNAPSHOT_MODULE: h.snapshot_module,
    QueryMethod.SNAPSHOT_FILE: h.snapshot_file,
    QueryMethod.GRAPH: h.graph,
    QueryMethod.EDGE_POINTS: h.edge_points,
    QueryMethod.EDGE_POINTS_BATCH: h.edge_points_batch,
    QueryMethod.EDGE_EVIDENCE: h.edge_evidence,
    QueryMethod.MODELS: h.models,
    QueryMethod.DEPENDS: h.depends,
    QueryMethod.FAILURES: h.failures,
    QueryMethod.EDGE_KIND_TIMESERIES: h.edge_kind_timeseries,
    QueryMethod.RELATIONS_DIFF: h.relations_diff,
}


def parse_query_method(method: str) -> QueryMethod | None:
    """Parse a string method name into a typed :class:`QueryMethod`, ``None`` if unknown."""
    try:
        return QueryMethod(method)
    except ValueError:
        return None


def build_status(
    *,
    reader: StoreReader | None,
    store_present: bool,
    writer_active: bool,
    schema_error: schema.SchemaIncompatibleError | None = None,
) -> schemas.StatusResponse:
    """Build the status response (mirror of the HTTP ``/status`` endpoint)."""
    resolved_version = schema_error.stored if schema_error is not None else schema.SCHEMA_VERSION
    compatible = schema_error is None
    if reader is None:
        return schemas.StatusResponse(
            project_id=None,
            branch=None,
            schema_version=resolved_version,
            expected_schema_version=schema.SCHEMA_VERSION,
            schema_compatible=compatible,
            store_present=store_present,
            writer_active=writer_active,
            commit_count=0,
            last_run=None,
            run_failures=[],
        )
    project = reader.get_project()
    last_run = reader.last_run()
    run_failures: list[schemas.RunFailureResponse] = []
    if last_run and last_run["commits_failed"] > 0:
        run_failures = [
            schemas.RunFailureResponse(**row) for row in reader.failures_for_run(last_run["run_id"])
        ]
    scope = None
    if project is not None:
        scope = schemas.ScopeResponse(
            project_label=project.scope.project_label,
            module_prefixes=list(project.scope.module_prefixes),
            include_modules=list(project.scope.include_modules),
            all_modules=project.scope.all_modules,
            repo_path=project.repo_path,
        )
    return schemas.StatusResponse(
        project_id=project.project_id if project is not None else None,
        branch=project.branch if project is not None else None,
        schema_version=reader.schema_version(),
        expected_schema_version=schema.SCHEMA_VERSION,
        schema_compatible=True,
        store_present=store_present,
        writer_active=writer_active,
        commit_count=reader.commit_count(),
        last_run=schemas.LastRunResponse(**last_run) if last_run else None,
        run_failures=run_failures,
        scope=scope,
    )


def dispatch(
    reader: StoreReader | None,
    method: str,
    params: dict,
    *,
    writer_active: bool = False,
    store_present: bool = True,
    schema_error: schema.SchemaIncompatibleError | None = None,
) -> Any:
    """Resolve one dashboard read to its schema model(s) or raise ``QueryError``.

    Owns every method including ``status``. The caller opens the reader (or
    captures a schema error) and passes transport-specific context; this module
    centralizes method dispatch via a typed :class:`QueryMethod` enum, the
    writer-lock check, and error normalization.
    """
    typed = parse_query_method(method)
    if typed is None:
        raise_query_failure(
            QueryErrorCode.METHOD_NOT_FOUND, f"unknown method: {method}", http_status=404
        )
    match typed:
        case QueryMethod.STATUS:
            return build_status(
                reader=reader,
                store_present=store_present,
                writer_active=writer_active,
                schema_error=schema_error,
            )
        case _:
            pass
    if writer_active:
        raise_query_failure(QueryErrorCode.LOCKED, "analysis in progress", http_status=409)
    if schema_error is not None:
        raise QueryError("SCHEMA_INCOMPATIBLE", str(schema_error), http_status=503)
    if reader is None:
        raise QueryError("STORE_NOT_FOUND", "store not found", http_status=503)
    handler = _METHOD_TABLE[typed]
    try:
        return handler(reader, params)
    except QueryError:
        raise
    except QueryNotFoundError as exc:
        raise QueryError("QUERY_NOT_FOUND", str(exc), http_status=404) from exc
    except schema.SchemaIncompatibleError as exc:
        raise QueryError("SCHEMA_INCOMPATIBLE", str(exc), http_status=503) from exc
    except Exception as exc:  # noqa: BLE001
        raise QueryError("INTERNAL", str(exc), http_status=500) from exc
