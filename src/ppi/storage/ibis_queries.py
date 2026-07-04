"""Ibis expression builders for history run/status/read-model queries.

These are pure, typed functions that construct lazy Ibis expressions.
They do not execute, open connections, or construct SQL strings.
"""

from __future__ import annotations

import ibis
import ibis.expr.types as ir


def select_project(project: ir.Table) -> ir.Table:
    return project.select(
        "project_id",
        "repo_path",
        "branch",
        "profile",
        "project_label",
        "module_prefixes",
        "include_modules",
        "all_modules",
    ).limit(1)


def select_commit_timeline(commit: ir.Table) -> ir.Table:
    return commit.select(
        "commit_hash",
        "commit_order",
        "authored_at",
        "summary",
    ).order_by(commit.commit_order)


def select_module_aggregate_snapshot(
    module_aggregate: ir.Table,
    commit_hash: str,
) -> ir.Table:
    return module_aggregate.filter(
        module_aggregate.commit_hash == commit_hash,
    ).select(
        "module_name",
        "total_lines",
        "metrics",
        "line_counts",
        "distributions",
    ).order_by("module_name")


def select_file_metric_snapshot(
    file_metric: ir.Table,
    commit_hash: str,
    module_name: str | None = None,
) -> ir.Table:
    filtered = file_metric.filter(file_metric.commit_hash == commit_hash)
    if module_name is not None:
        filtered = filtered.filter(filtered.module_name == module_name)
    return filtered.select(
        "module_name",
        "relative_path",
        "line_category_id",
        "metrics",
        "line_counts",
        "distributions",
    ).order_by(["module_name", "relative_path"])


def select_latest_commit_hash(commit: ir.Table) -> ir.Table:
    return commit.order_by(ibis.desc("commit_order")).limit(1).select("commit_hash")


def select_latest_snapshot(
    table: ir.Table,
    commit: ir.Table,
    extra_cols: list[str] | None = None,
) -> ir.Table:
    latest = commit.order_by(ibis.desc("commit_order")).limit(1)
    joined = table.join(latest, table.commit_hash == latest.commit_hash)
    base_cols = ["module_name", "metrics", "line_counts"]
    if "total_lines" in table.columns:
        base_cols.insert(1, "total_lines")
    cols = base_cols
    if extra_cols:
        cols = list(dict.fromkeys(cols + extra_cols))
    return joined.select(*[joined[c] for c in cols])


def select_graph_nodes(
    module_aggregate: ir.Table,
    commit_hash: str,
) -> ir.Table:
    return module_aggregate.filter(
        module_aggregate.commit_hash == commit_hash
    ).select(
        module_aggregate.module_name,
        module_aggregate.total_lines,
        module_aggregate.metrics,
        module_aggregate.line_counts,
    )


def select_graph_edges(
    coupling_edge: ir.Table,
    commit_hash: str,
    include_zero_score: bool = False,
) -> ir.Table:
    expr = coupling_edge.filter(coupling_edge.commit_hash == commit_hash)
    if not include_zero_score:
        expr = expr.filter(expr.score > 0)
    return expr.select(
        coupling_edge.source_module.name("source"),
        coupling_edge.target_module.name("target"),
        coupling_edge.score,
        coupling_edge.kinds,
        coupling_edge.kind_occurrence_count,
        coupling_edge.breakdown,
        ibis.literal(commit_hash).name("commit_hash"),
    ).order_by(ibis.desc("score"))


def select_module_metric_timeseries(
    module_aggregate: ir.Table,
    commit: ir.Table,
    module_name: str,
    metric_key: str,
) -> ir.Table:
    with_val = module_aggregate.mutate(_value=module_aggregate["metrics"][metric_key].cast(float))
    joined = with_val.join(commit, with_val.commit_hash == commit.commit_hash)
    filtered = joined.filter(joined.module_name == module_name)
    return filtered.select(
        filtered.commit_order,
        filtered.commit_hash,
        filtered._value.name("value"),
    ).order_by(filtered.commit_order)


def select_file_metric_timeseries(
    file_metric: ir.Table,
    commit: ir.Table,
    module_name: str,
    relative_path: str,
    metric_key: str,
) -> ir.Table:
    with_val = file_metric.mutate(_value=file_metric["metrics"][metric_key].cast(float))
    joined = with_val.join(commit, with_val.commit_hash == commit.commit_hash)
    filtered = joined.filter(
        joined.module_name == module_name,
        joined.relative_path == relative_path,
    )
    return filtered.select(
        filtered.commit_order,
        filtered.commit_hash,
        filtered._value.name("value"),
    ).order_by(filtered.commit_order)


def select_relations(
    coupling_edge: ir.Table,
    commit_hash: str,
    include_zero_score: bool = False,
) -> ir.Table:
    expr = coupling_edge.filter(coupling_edge.commit_hash == commit_hash)
    if not include_zero_score:
        expr = expr.filter(expr.score > 0)
    return expr.select(
        coupling_edge.source_module.name("source_id"),
        coupling_edge.source_module.name("source_label"),
        coupling_edge.target_module.name("target_id"),
        coupling_edge.target_module.name("target_label"),
        ibis.literal("").name("relation_type_id"),
        ibis.literal("").name("relation_type_label"),
        ibis.literal("").name("strength_metric_id"),
        ibis.literal("").name("strength_metric_label"),
        coupling_edge.score.cast(float).name("strength_value"),
        ibis.literal(commit_hash).name("commit_hash"),
    ).order_by(ibis.desc("strength_value"))
