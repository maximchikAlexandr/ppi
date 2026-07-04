"""Endpoint handlers — all queries go through the Ibis pipeline.

Each handler returns ``Result[Response, DomainError]``; only the outermost
adapter (CLI/HTTP/RPC) converts to an exception or error response.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from ppi.core.errors import DomainError, ErrorCategory, ErrorCode
from ppi.core.result import Error, Ok, Result
from ppi.query import metric_catalog, schemas
from ppi.query._params import QueryError, _opt_bool, _opt_str, _req
from ppi.query.contracts import QueryParams


def _to_domain_error(exc: QueryError) -> DomainError:
    return DomainError(
        code=_QUERY_TO_ERROR_CODE.get(exc.code, ErrorCode.QUERY_ERROR),
        category=ErrorCategory.QUERY,
        message=exc.message,
        details=(("http_status", exc.http_status), ("code", exc.code)),
    )


_QUERY_TO_ERROR_CODE: dict[str, ErrorCode] = {
    "INVALID_PARAMS": ErrorCode.VALIDATION_ERROR,
    "QUERY_NOT_FOUND": ErrorCode.QUERY_ERROR,
    "QUERY_ERROR": ErrorCode.UNEXPECTED_ERROR,
    "SCHEMA_INCOMPATIBLE": ErrorCode.SCHEMA_ERROR,
    "STORE_NOT_FOUND": ErrorCode.STORAGE_ERROR,
    "LOCKED": ErrorCode.LOCK_ERROR,
    "METHOD_NOT_FOUND": ErrorCode.QUERY_ERROR,
    "INTERNAL": ErrorCode.UNEXPECTED_ERROR,
}


def _run(store_file: Path, metric: str, **kw: Any) -> Result[Any, DomainError]:
    from ppi.query.pipeline import run_query
    return run_query(store_file, QueryParams(metric=metric, **kw))


def commits(store_file: Path, params: dict) -> Result[list[schemas.CommitResponse], DomainError]:
    r = _run(store_file, "commits")
    return r.map(lambda rows: [schemas.CommitResponse(**row) for row in rows])


def metrics_timeseries(
    store_file: Path, params: dict,
) -> Result[schemas.TimeseriesResponse, DomainError]:
    try:
        level = _req(params, "level")
        metric_id = _req(params, "metric_id")
        try:
            metric_id = metric_catalog.validate_metric_id(metric_id, level=level)
        except ValueError as exc:
            raise QueryError("INVALID_PARAMS", str(exc), http_status=422) from exc
        agg = _req(params, "agg")
        name = _opt_str(params, "name")
        if not name:
            raise QueryError(
                "INVALID_PARAMS",
                f"name is required for {level} level",
                http_status=422,
            )
    except QueryError as exc:
        return Error(_to_domain_error(exc))

    if level == "module":
        r = _run(store_file, "module-timeseries", module_name=name, metric_id=metric_id, agg=agg)
    else:
        module_name, _, relative_path = name.partition("/")
        if not module_name or not relative_path:
            return Error(DomainError(
                code=ErrorCode.VALIDATION_ERROR, category=ErrorCategory.QUERY,
                message="file name must be module/relative/path",
                details=(("http_status", 422), ("code", "INVALID_PARAMS")),
            ))
        r = _run(
            store_file,
            "file-timeseries",
            module_name=module_name,
            file_path=relative_path,
            metric_id=metric_id,
            agg=agg,
        )

    return r.bind(lambda rows: _build_timeseries_response(level, metric_id, agg, name, rows))


def _build_timeseries_response(
    level: str, metric_id: str, agg: str, name: str, rows: list[dict],
) -> Result[schemas.TimeseriesResponse, DomainError]:
    if not rows:
        return Error(DomainError(
            ErrorCode.QUERY_ERROR, ErrorCategory.QUERY,
            f"unknown {level}: {name}",
            details=(("http_status", 404), ("code", "QUERY_NOT_FOUND")),
        ))
    return Ok(schemas.TimeseriesResponse(
        level=level, metric_id=metric_id, agg=agg,
        series=[schemas.TimeseriesSeriesResponse(
            name=name,
            points=[schemas.TimeseriesPointResponse(**p) for p in rows],
        )],
    ))


def hotspots(store_file: Path, params: dict) -> Result[schemas.HotspotsResponse, DomainError]:
    try:
        metric_id = _req(params, "metric_id")
        by = _req(params, "by")
        level = _req(params, "level")
        agg = _req(params, "agg")
        limit = int(params.get("limit", 20))
    except QueryError as exc:
        return Error(_to_domain_error(exc))

    r = _run(store_file, "hotspots", metric_id=metric_id, agg=agg, level=level, limit=limit)
    return r.map(lambda items: schemas.HotspotsResponse(
        by=by, items=[schemas.HotspotItemResponse(**it) for it in items],
    ))


def graph(store_file: Path, params: dict) -> Result[schemas.GraphResponse, DomainError]:
    r = _run(
        store_file, "graph",
        commit_hash=_opt_str(params, "commit"),
        include_zero_score=_opt_bool(params, "include_zero_score", False),
    )
    return r.map(lambda data: schemas.GraphResponse(
        commit_hash=data.get("commit_hash", ""),
        nodes=[schemas.GraphNodeResponse(**n) for n in data.get("nodes", [])],
        edges=[schemas.EdgeResponse(**e) for e in data.get("edges", [])],
    ))


def ui_config(store_file: Path, params: dict) -> Result[schemas.UiConfigResponse, DomainError]:
    catalog_metrics = [_ui_metric_option_from_metric(m) for m in metric_catalog.all_metrics()]
    return Ok(schemas.UiConfigResponse(
        dashboard_metrics=catalog_metrics,
        aggregations=[_ui_option(a) for a in metric_catalog.aggregations()],
        tables=_TABLE_DEFINITIONS,
        graph=schemas.UiGraphConfig(
            edge_types=[_ui_option(r) for r in metric_catalog.relation_types()],
            line_categories=[_ui_option(option) for option in metric_catalog.line_categories()],
            brightness_metrics=catalog_metrics,
            node_size_metrics=[
                _ui_metric_option_from_graph(option)
                for option in metric_catalog.node_size_options()
            ],
            link_thickness_metrics=[
                _ui_metric_option_from_graph(option)
                for option in metric_catalog.link_thickness_options()
            ],
        ),
    ))


def _ui_option(o: metric_catalog.Option) -> schemas.UiOption:
    return schemas.UiOption(id=o.id, label=o.label, default_enabled=o.default_enabled)


def _ui_metric_option_from_metric(m: metric_catalog.MetricDefinition) -> schemas.UiMetricOption:
    supported: list[Literal["module", "file"]] = []
    if m.reader_method_module is not None:
        supported.append("module")
    if m.reader_method_file is not None:
        supported.append("file")
    return schemas.UiMetricOption(
        id=m.metric_id, label=m.label, unit=m.unit or "", format=m.format or "",
        default_enabled=m.default_enabled, supported_levels=supported,
    )


def _ui_metric_option_from_graph(o: metric_catalog.GraphViewOption) -> schemas.UiMetricOption:
    return schemas.UiMetricOption(
        id=o.id,
        label=o.label,
        format="d",
        default_enabled=o.default_enabled,
    )


def _file_table_columns() -> tuple[schemas.UiColumnDefinition, ...]:
    columns: list[schemas.UiColumnDefinition] = [
        schemas.UiColumnDefinition(key="relative_path", label="File", type="string"),
        schemas.UiColumnDefinition(key="line_category_id", label="Category", type="string"),
    ]
    for metric in metric_catalog.all_metrics():
        if metric.reader_method_file is None:
            continue
        if metric.metric_id == "lines":
            columns.append(schemas.UiColumnDefinition(
                key="line_counts.lines",
                label=metric.label,
                type="number",
                metric_id=metric.metric_id,
            ))
        elif metric.metric_id in {"function_count", "jones_line_count"}:
            columns.append(schemas.UiColumnDefinition(
                key=f"line_counts.{metric.metric_id}",
                label=metric.label,
                type="number",
                metric_id=metric.metric_id,
            ))
        else:
            for agg in metric_catalog.aggregations():
                columns.append(schemas.UiColumnDefinition(
                    key=f"metrics.{metric.metric_id}_{agg.id}",
                    label=f"{metric.label} {agg.label}",
                    type="number",
                    metric_id=metric.metric_id,
                ))
    return tuple(columns)


_TABLE_DEFINITIONS: tuple[schemas.UiTableDefinition, ...] = (
    schemas.UiTableDefinition(key="modules", label="Modules", columns=(
        schemas.UiColumnDefinition(key="module_name", label="Module", type="string"),
        schemas.UiColumnDefinition(key="total_lines", label="Lines", type="number"),
        schemas.UiColumnDefinition(key="line_counts", label="Line counts", type="json"),
    )),
    schemas.UiTableDefinition(key="files", label="Files", columns=_file_table_columns()),
    schemas.UiTableDefinition(key="relations", label="Relations", columns=(
        schemas.UiColumnDefinition(key="source_id", label="Source", type="string"),
        schemas.UiColumnDefinition(key="relation_type_id", label="Type", type="string"),
        schemas.UiColumnDefinition(key="relation_type_label", label="Type label", type="string"),
        schemas.UiColumnDefinition(key="target_id", label="Target", type="string"),
        schemas.UiColumnDefinition(key="strength_metric_label", label="Strength", type="string"),
        schemas.UiColumnDefinition(key="strength_value", label="Strength value", type="number"),
    )),
)


def snapshot_table_modules(
    store_file: Path, params: dict,
) -> Result[schemas.GenericTableResponse, DomainError]:
    commit = _opt_str(params, "commit")
    r = _run(store_file, "snapshot-table-modules", commit_hash=commit)
    return r.map(lambda data: schemas.GenericTableResponse(
        commit_hash=data.get("commit_hash", ""),
        rows=[schemas.GenericTableRow(
            id=str(r.get("module_name", "")), cells=r, actions={"drilldown": True},
        ) for r in data.get("rows", [])],
    ))


def snapshot_table_files(
    store_file: Path, params: dict,
) -> Result[schemas.GenericTableResponse, DomainError]:
    commit = _opt_str(params, "commit")
    module_name = _opt_str(params, "module_name")
    r = _run(store_file, "snapshot-table-files", commit_hash=commit, module_name=module_name)
    return r.map(lambda data: schemas.GenericTableResponse(
        commit_hash=data.get("commit_hash", ""),
        rows=[schemas.GenericTableRow(cells=r, actions={}) for r in data.get("rows", [])],
    ))


def snapshot_relations(
    store_file: Path, params: dict,
) -> Result[schemas.RelationsResponse, DomainError]:
    commit = _opt_str(params, "commit")
    include_zero_score = _opt_bool(params, "include_zero_score", False)
    r = _run(
        store_file,
        "snapshot-relations",
        commit_hash=commit,
        include_zero_score=include_zero_score,
    )
    return r.map(lambda rows: schemas.RelationsResponse(
        commit_hash=rows[0].get("commit_hash", "") if rows else "",
        relations=[schemas.RelationRowResponse(**r) for r in rows],
    ))
