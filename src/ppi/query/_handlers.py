"""Endpoint handlers for the shared query dispatcher.

Each handler maps one dashboard method to its ``StoreReader`` call(s) and
shapes the result into a ``schemas`` model. The dispatcher (``dispatch.py``)
owns the router table and calls these by method name.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from ppi.query import schemas
from ppi.query._params import QueryError, _choice, _opt_bool, _opt_int, _opt_str, _req
from ppi.runtime.names import parse_module_file_path
from ppi.storage.queries import StoreReader

MAX_EDGE_POINTS_BATCH_PAIRS = 500


def commits(reader: StoreReader, params: dict) -> list[schemas.CommitResponse]:
    return [schemas.CommitResponse(**row) for row in reader.commits()]


def catalog(reader: StoreReader, params: dict) -> schemas.CatalogResponse:
    level = _choice(params, "level", {"module", "file"})
    limit = _opt_int(params, "limit", 5000)
    if level == "module":
        names = reader.list_module_names()
    else:
        names = reader.list_file_names(limit=limit)
    return schemas.CatalogResponse(level=level, names=names[:limit])


def metrics_timeseries(reader: StoreReader, params: dict) -> schemas.TimeseriesResponse:
    level = _choice(params, "level", {"module", "file"})
    metric = _choice(
        params,
        "metric",
        {"cyclomatic", "cognitive", "jones", "lines", "lines_by_category", "python_file_count"},
    )
    name = _opt_str(params, "name")
    agg = _choice(params, "agg", {"mean", "median", "p95", "max"}, default="mean")
    if level == "module":
        if not name:
            raise QueryError("INVALID_PARAMS", "name is required for module level", http_status=422)
        if not reader.module_exists(name):
            raise QueryError("QUERY_NOT_FOUND", f"unknown module: {name}", http_status=404)
        if metric == "lines":
            points = reader.module_lines_timeseries(name)
        elif metric == "lines_by_category":
            rows = reader.module_lines_by_category_timeseries(name)
            by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in rows:
                by_category[row["category"]].append(
                    {
                        "commit_order": row["commit_order"],
                        "commit_hash": row["commit_hash"],
                        "value": row["value"],
                    },
                )
            return schemas.TimeseriesResponse(
                level="module",
                metric=metric,
                agg=agg,
                series=[
                    schemas.TimeseriesSeriesResponse(
                        name=f"{name}/{category}",
                        points=[schemas.TimeseriesPointResponse(**point) for point in points],
                    )
                    for category, points in sorted(by_category.items())
                ],
            )
        elif metric == "python_file_count":
            points = reader.python_file_count_timeseries(name)
            return schemas.TimeseriesResponse(
                level="module",
                metric=metric,
                agg=agg,
                series=[
                    schemas.TimeseriesSeriesResponse(
                        name=name,
                        points=[schemas.TimeseriesPointResponse(**point) for point in points],
                    )
                ],
            )
        else:
            points = reader.module_complexity_timeseries(name, metric=metric, agg=agg)
        if not points:
            raise QueryError("QUERY_NOT_FOUND", f"unknown module: {name}", http_status=404)
        return schemas.TimeseriesResponse(
            level="module",
            metric=metric,
            agg=agg,
            series=[
                schemas.TimeseriesSeriesResponse(
                    name=name,
                    points=[schemas.TimeseriesPointResponse(**point) for point in points],
                )
            ],
        )
    if not name:
        raise QueryError("INVALID_PARAMS", "name is required for file level", http_status=422)
    try:
        module_name, relative_path = parse_module_file_path(name)
    except ValueError as exc:
        raise QueryError("INVALID_PARAMS", str(exc), http_status=422) from exc
    if not reader.file_exists(module_name, relative_path):
        raise QueryError("QUERY_NOT_FOUND", f"unknown file: {name}", http_status=404)
    if metric == "lines":
        points = reader.file_lines_timeseries(module_name, relative_path)
    else:
        points = reader.file_complexity_timeseries(
            module_name, relative_path, metric=metric, agg=agg
        )
    if not points:
        raise QueryError("QUERY_NOT_FOUND", f"unknown file: {name}", http_status=404)
    return schemas.TimeseriesResponse(
        level="file",
        metric=metric,
        agg=agg,
        series=[
            schemas.TimeseriesSeriesResponse(
                name=name,
                points=[schemas.TimeseriesPointResponse(**point) for point in points],
            )
        ],
    )


def hotspots(reader: StoreReader, params: dict) -> schemas.HotspotsResponse:
    level = _choice(params, "level", {"module", "file"}, default="module")
    metric = _choice(
        params,
        "metric",
        {"cyclomatic", "cognitive", "jones", "python_file_count"},
        default="cyclomatic",
    )
    by = _choice(params, "by", {"value", "growth"}, default="value")
    limit = _opt_int(params, "limit", 20)
    agg = _choice(params, "agg", {"mean", "median", "p95", "max"}, default="mean")
    return schemas.HotspotsResponse(
        by=by,
        items=[
            schemas.HotspotItemResponse(**item)
            for item in reader.hotspots(level=level, metric=metric, by=by, limit=limit, agg=agg)
        ],
    )


def structure_timeseries(reader: StoreReader, params: dict) -> schemas.StructureTimeseriesResponse:
    include_zero_score = _opt_bool(params, "include_zero_score", False)
    points = reader.coupling_structure_timeseries(include_zero_score=include_zero_score)
    return schemas.StructureTimeseriesResponse(
        points=[schemas.StructurePointResponse(**point) for point in points]
    )


def edges(reader: StoreReader, params: dict) -> schemas.EdgesResponse:
    commit = _opt_str(params, "commit")
    min_score = _opt_int(params, "min_score", 0)
    include_zero_score = _opt_bool(params, "include_zero_score", False)
    if commit and not reader.commit_exists(commit):
        raise QueryError("QUERY_NOT_FOUND", f"unknown commit: {commit}", http_status=404)
    rows = reader.edges_at_commit(commit, include_zero_score=include_zero_score)
    resolved_commit = commit or reader.latest_edge_commit_hash() or reader.latest_commit_hash()
    if resolved_commit is None:
        return schemas.EdgesResponse(commit_hash=None, edges=[])
    threshold = min_score if include_zero_score else max(min_score, 1)
    filtered = [row for row in rows if row["score"] >= threshold]
    return schemas.EdgesResponse(
        commit_hash=resolved_commit, edges=[schemas.EdgeResponse(**row) for row in filtered]
    )


def snapshot_modules(reader: StoreReader, params: dict) -> schemas.ModuleSnapshotResponse:
    return schemas.ModuleSnapshotResponse(**reader.modules_at_commit(_opt_str(params, "commit")))


def snapshot_files(reader: StoreReader, params: dict) -> schemas.FileSnapshotResponse:
    return schemas.FileSnapshotResponse(
        **reader.files_at_commit(_opt_str(params, "commit"), _opt_str(params, "module"))
    )


def snapshot_module(reader: StoreReader, params: dict) -> schemas.ModuleDetailResponse:
    return schemas.ModuleDetailResponse(
        **reader.module_detail(_req(params, "module"), _opt_str(params, "commit"))
    )


def snapshot_file(reader: StoreReader, params: dict) -> schemas.FileDetailResponse:
    name = _req(params, "name")
    try:
        module_name, relative_path = parse_module_file_path(name)
    except ValueError as exc:
        raise QueryError("INVALID_PARAMS", str(exc), http_status=422) from exc
    payload = reader.file_detail(module_name, relative_path, _opt_str(params, "commit"))
    return schemas.FileDetailResponse(
        commit_hash=payload["commit_hash"], file=schemas.FileSnapshotItemResponse(**payload["file"])
    )


def graph(reader: StoreReader, params: dict) -> schemas.GraphResponse:
    return schemas.GraphResponse(
        **reader.graph_at_commit(
            _opt_str(params, "commit"),
            include_zero_score=_opt_bool(params, "include_zero_score", False),
        )
    )


def edge_points(reader: StoreReader, params: dict) -> schemas.EdgePointsResponse:
    return schemas.EdgePointsResponse(
        **reader.edge_points(
            _req(params, "source"),
            _req(params, "target"),
            _opt_str(params, "commit"),
            include_zero_score=_opt_bool(params, "include_zero_score", False),
        )
    )


def edge_points_batch(reader: StoreReader, params: dict) -> schemas.EdgePointsBatchResponse:
    pairs_raw = params.get("pairs")
    if not isinstance(pairs_raw, list):
        raise QueryError("INVALID_PARAMS", "pairs is required", http_status=422)
    pairs: list[tuple[str, str]] = []
    for pair in pairs_raw:
        if not isinstance(pair, dict) or "source" not in pair or "target" not in pair:
            raise QueryError("INVALID_PARAMS", "each pair needs source and target", http_status=422)
        pairs.append((str(pair["source"]), str(pair["target"])))
    if len(pairs) > MAX_EDGE_POINTS_BATCH_PAIRS:
        raise QueryError(
            "INVALID_PARAMS",
            f"At most {MAX_EDGE_POINTS_BATCH_PAIRS} pairs per batch request",
            http_status=422,
        )
    payload = reader.edge_points_batch(
        pairs,
        _opt_str(params, "commit"),
        include_zero_score=_opt_bool(params, "include_zero_score", False),
    )
    return schemas.EdgePointsBatchResponse(
        commit_hash=payload["commit_hash"],
        edges=[schemas.EdgePointsResponse(**edge) for edge in payload["edges"]],
        missing=[schemas.EdgePointsMissingPairResponse(**row) for row in payload["missing"]],
    )


def edge_evidence(reader: StoreReader, params: dict) -> schemas.EdgeEvidenceResponse:
    return schemas.EdgeEvidenceResponse(
        **reader.edge_evidence_for_pair(
            _req(params, "source"),
            _req(params, "target"),
            _opt_str(params, "commit"),
            include_zero_score=_opt_bool(params, "include_zero_score", False),
        )
    )


def models(reader: StoreReader, params: dict) -> schemas.ModuleModelsResponse:
    return schemas.ModuleModelsResponse(
        **reader.module_models(_req(params, "module"), _opt_str(params, "commit"))
    )


def depends(reader: StoreReader, params: dict) -> schemas.ManifestDependsResponse:
    return schemas.ManifestDependsResponse(
        **reader.manifest_depends(_opt_str(params, "module"), _opt_str(params, "commit"))
    )


def failures(reader: StoreReader, params: dict) -> schemas.FailuresResponse:
    return schemas.FailuresResponse(**reader.failures_at_commit(_opt_str(params, "commit")))


def edge_kind_timeseries(reader: StoreReader, params: dict) -> schemas.EdgeKindSeriesResponse:
    return schemas.EdgeKindSeriesResponse(
        points=[
            schemas.EdgeKindSeriesPointResponse(**row)
            for row in reader.edge_kind_timeseries(_opt_str(params, "kind"))
        ],
    )


def relations_diff(reader: StoreReader, params: dict) -> schemas.RelationsDiffResponse:
    return schemas.RelationsDiffResponse(
        **reader.relations_diff(_req(params, "commit_a"), _req(params, "commit_b"))
    )