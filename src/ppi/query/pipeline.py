"""Query pipeline: validated params -> Ibis expression -> result DTO.

Routes every query family through pure Ibis expression builders.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ppi.core.errors import DomainError, ErrorCategory, ErrorCode
from ppi.core.result import Error, Nothing, Ok, Option, Result, Some
from ppi.query.contracts import QueryParams
from ppi.storage.ibis_backend import connect_ibis, disconnect_ibis, execute_expr, load_table
from ppi.storage.ibis_queries import (
    select_commit_timeline,
    select_file_metric_snapshot,
    select_file_metric_timeseries,
    select_graph_edges,
    select_graph_nodes,
    select_latest_commit_hash,
    select_latest_snapshot,
    select_module_aggregate_snapshot,
    select_module_metric_timeseries,
    select_project,
    select_relations,
)


def _latest_commit_hash(backend) -> Option[str]:
    table_r = load_table(backend, "commit")
    if table_r.is_error():
        return Nothing
    r = execute_expr(backend, select_latest_commit_hash(table_r.ok))
    if r.is_error() or not r.ok:
        return Nothing
    return Some(r.ok[0].get("commit_hash", ""))


def _metric_key(metric: str, agg: str) -> str:
    return metric if metric.endswith(f"_{agg}") else f"{metric}_{agg}"


def run_query(store_file: Path, params: QueryParams) -> Result[Any, DomainError]:
    backend_result = connect_ibis(store_file)
    if backend_result.is_error():
        return Error(backend_result.error)
    backend = backend_result.ok
    try:
        match params.metric:
            case "project-info":
                table = load_table(backend, "project")
                if table.is_error():
                    return Error(table.error)
                result = execute_expr(backend, select_project(table.ok))
                if result.is_error():
                    return Error(result.error)
                return Ok(result.ok)

            case "commits":
                table = load_table(backend, "commit")
                if table.is_error():
                    return Error(table.error)
                result = execute_expr(backend, select_commit_timeline(table.ok))
                if result.is_error():
                    return Error(result.error)
                return Ok(result.ok)

            case "snapshot-table-modules":
                ch = params.commit_hash or _latest_commit_hash(backend).default_value(None)
                if ch is None:
                    return Error(DomainError(code=ErrorCode.QUERY_ERROR, category=ErrorCategory.QUERY, message="No commits in store"))
                table = load_table(backend, "module_aggregate")
                if table.is_error():
                    return Error(table.error)
                expr = select_module_aggregate_snapshot(table.ok, ch)
                result = execute_expr(backend, expr)
                if result.is_error():
                    return Error(result.error)
                return Ok({"commit_hash": ch, "rows": _parse_json_cols(result.ok)})

            case "snapshot-table-files":
                ch = params.commit_hash or _latest_commit_hash(backend).default_value(None)
                if ch is None:
                    return Error(DomainError(code=ErrorCode.QUERY_ERROR, category=ErrorCategory.QUERY, message="No commits in store"))
                table = load_table(backend, "file_metric")
                if table.is_error():
                    return Error(table.error)
                expr = select_file_metric_snapshot(table.ok, ch, params.module_name)
                result = execute_expr(backend, expr)
                if result.is_error():
                    return Error(result.error)
                return Ok({"commit_hash": ch, "rows": _parse_json_cols(result.ok)})

            case "module-timeseries":
                table = load_table(backend, "module_aggregate")
                if table.is_error():
                    return Error(table.error)
                commit_t = load_table(backend, "commit")
                if commit_t.is_error():
                    return Error(commit_t.error)
                key = _metric_key(params.metric_id or "cyclomatic", params.agg or "mean")
                expr = select_module_metric_timeseries(table.ok, commit_t.ok, params.module_name or "", key)
                result = execute_expr(backend, expr)
                if result.is_error():
                    return Error(result.error)
                return Ok(result.ok)

            case "file-timeseries":
                table = load_table(backend, "file_metric")
                if table.is_error():
                    return Error(table.error)
                commit_t = load_table(backend, "commit")
                if commit_t.is_error():
                    return Error(commit_t.error)
                key = _metric_key(params.metric_id or "cyclomatic", params.agg or "mean")
                expr = select_file_metric_timeseries(table.ok, commit_t.ok, params.module_name or "", params.file_path or "", key)
                result = execute_expr(backend, expr)
                if result.is_error():
                    return Error(result.error)
                return Ok(result.ok)

            case "hotspots":
                commit_t = load_table(backend, "commit")
                if commit_t.is_error():
                    return Error(commit_t.error)
                key = _metric_key(params.metric_id or "cyclomatic", params.agg or "mean")
                data_table = load_table(backend, "file_metric" if params.level == "file" else "module_aggregate")
                if data_table.is_error():
                    return Error(data_table.error)
                extra = ["relative_path"] if params.level == "file" else None
                rows = execute_expr(backend, select_latest_snapshot(data_table.ok, commit_t.ok, extra))
                if rows.is_error():
                    return Error(rows.error)
                items = _build_hotspots(rows.ok, key, params.level, params.limit)
                return Ok(items)

            case "graph":
                ch = params.commit_hash or _latest_commit_hash(backend).default_value(None)
                if ch is None:
                    return Error(DomainError(code=ErrorCode.QUERY_ERROR, category=ErrorCategory.QUERY, message="No commits in store"))
                ma_t = load_table(backend, "module_aggregate")
                if ma_t.is_error():
                    return Error(ma_t.error)
                ce_t = load_table(backend, "coupling_edge")
                if ce_t.is_error():
                    return Error(ce_t.error)
                nodes = execute_expr(backend, select_graph_nodes(ma_t.ok, ch))
                if nodes.is_error():
                    return Error(nodes.error)
                edges = execute_expr(backend, select_graph_edges(ce_t.ok, ch, params.include_zero_score))
                if edges.is_error():
                    return Error(edges.error)
                return Ok({"commit_hash": ch, "nodes": _parse_json_cols(nodes.ok), "edges": _parse_json_cols(edges.ok)})

            case "snapshot-relations":
                ch = params.commit_hash or _latest_commit_hash(backend).default_value(None)
                if ch is None:
                    return Error(DomainError(code=ErrorCode.QUERY_ERROR, category=ErrorCategory.QUERY, message="No commits in store"))
                table = load_table(backend, "coupling_edge")
                if table.is_error():
                    return Error(table.error)
                expr = select_relations(table.ok, ch, params.include_zero_score)
                result = execute_expr(backend, expr)
                if result.is_error():
                    return Error(result.error)
                return Ok(result.ok)

            case _:
                return Error(DomainError(code=ErrorCode.QUERY_ERROR, category=ErrorCategory.QUERY, message=f"Unknown metric: {params.metric}"))
    finally:
        disconnect_ibis(store_file)


def _parse_json_cols(rows: list[dict]) -> list[dict]:
    parsed = []
    for row in rows:
        r = {}
        for k, v in row.items():
            if isinstance(v, str) and k in ("metrics", "line_counts", "distributions", "kinds", "breakdown"):
                try:
                    r[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    r[k] = v
            else:
                r[k] = v
        parsed.append(r)
    return parsed


def _build_hotspots(rows: list[dict], metric_key: str, level: str, limit_n: int) -> list[dict]:
    items = []
    for row in rows:
        metrics = row.get("metrics", {})
        if isinstance(metrics, str):
            metrics = json.loads(metrics)
        value = metrics.get(metric_key) if isinstance(metrics, dict) else None
        if value is not None:
            name = row.get("module_name", "")
            if level == "file":
                name = f"{name}/{row.get('relative_path', '')}"
            items.append({"name": name, "current": float(value), "first": None, "growth": None})
    items.sort(key=lambda x: x["current"], reverse=True)
    return items[:limit_n]
