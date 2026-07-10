"""Generic backend projection layer for ``/api/v1``.

ponytail: the only backend generic projection layer (spec task T174).
Returns plain snake_case dicts; the FastAPI boundary (CamelModel alias
generator in src/ppi/server/v1_schemas.py) is the SOLE camelCase authority.
No FastAPI/Pydantic imports here, no camelCase string literals — add a
field to the Pydantic model and it flows through the alias generator.

Functions:
* build_ui_config_projection      — entity kinds, metrics, relation types,
  line categories, tables, queries, graph lenses, visual encodings
  (sourced from metric_catalog, the plugin-shaped registry).
* build_commits_projection        — list of commit summaries.
* build_entity_projection         — entity targets by entity kind.
* build_graph_projection          — generic graph nodes/edges.
* build_table_modules_projection  — modules table (columns + drilldown rows).
* build_table_files_projection    — files table filtered by parent module.
* build_table_relations_projection — relations-as-table projection.
* build_tables_index_projection   — list of available table definitions.
* build_timeseries_projection     — metric timeseries series.
* build_hotspots_projection       — metric hotspot ranking.
"""

from __future__ import annotations

from typing import Any

from ppi.query import metric_catalog
from ppi.query.profile_kinds import (
    PYTHON_FILE_KIND,
    PYTHON_MODULE_KIND,
)

_TABLE_MODULES_ID: str = "entities.modules"
_TABLE_FILES_ID: str = "entities.files"
_TABLE_RELATIONS_ID: str = "relations.current"


def build_ui_config_projection() -> dict[str, Any]:
    """Assemble the UI config from the metric catalog (the registry).

    The catalog is the single source of truth for metrics, relation types,
    line categories and aggregations; this function only adapts catalog
    rows to the public UiConfig shape. Adding a metric or relation type
    is a catalog change, not an edit here (Constitution III & IV).
    """
    metrics = [
        {
            "id": m.metric_id,
            "label": m.label,
            "value_type": m.value_type,
            "scope": m.scope,
            "entity_kinds": [PYTHON_MODULE_KIND, PYTHON_FILE_KIND],
            "supported_aggregations": [o.id for o in metric_catalog.aggregations()],
            "default_aggregation": "mean",
            "supported_views": ["graph", "table", "dashboard"],
            "higher_is_worse": m.metric_id in {"cyclomatic", "cognitive", "jones"},
            "format": {"kind": "decimal" if m.value_type == "number" else "integer"},
        }
        for m in metric_catalog.all_metrics()
    ]
    relation_types = [
        {
            "id": o.id,
            "label": o.label,
            "default_visible": o.default_enabled,
            "group": "code",
            "plugin_id": None,
        }
        for o in metric_catalog.relation_types()
    ]
    line_categories = [
        {
            "id": o.id,
            "label": o.label,
            "default_visible": o.default_enabled,
            "order": i,
        }
        for i, o in enumerate(metric_catalog.line_categories())
    ]
    tables = [
        {
            "id": _TABLE_MODULES_ID,
            "label": "Modules",
            "entity_kind_id": PYTHON_MODULE_KIND,
            "supported_actions": ["drilldown"],
            "default_sort": None,
        },
        {
            "id": _TABLE_FILES_ID,
            "label": "Files",
            "entity_kind_id": PYTHON_FILE_KIND,
            "supported_actions": ["drilldown"],
            "default_sort": None,
        },
        {
            "id": _TABLE_RELATIONS_ID,
            "label": "Relations",
            "entity_kind_id": None,
            "supported_actions": [],
            "default_sort": None,
        },
    ]
    graph_lenses = [
        {
            "id": "module-dependencies",
            "label": "Module dependencies",
            "node_kinds": [PYTHON_MODULE_KIND],
            "relation_types": [o.id for o in metric_catalog.relation_types()],
            "default_visual_encoding": {
                "node_size_encoding_id": "lines",
                "edge_thickness_encoding_id": "score",
            },
        }
    ]
    queries = [
        {
            "id": "metrics.timeseries",
            "label": "Metrics over time",
            "result_kind": "timeseries",
            "parameters": [
                {"id": "entityKindId", "label": "Entity kind", "kind": "entityKind", "required": True},
                {"id": "metricId", "label": "Metric", "kind": "metric", "required": True},
                {"id": "aggregation", "label": "Aggregation", "kind": "aggregation", "required": True},
                {"id": "targetId", "label": "Target", "kind": "target", "required": False},
            ],
        },
        {
            "id": "metrics.hotspots",
            "label": "Hotspots",
            "result_kind": "ranking",
            "parameters": [
                {"id": "entityKindId", "label": "Entity kind", "kind": "entityKind", "required": True},
                {"id": "metricId", "label": "Metric", "kind": "metric", "required": True},
                {"id": "aggregation", "label": "Aggregation", "kind": "aggregation", "required": True},
            ],
        },
    ]
    return {
        "schema_version": 1,
        "profile": {"id": "ppi.default", "label": "Default", "plugin_ids": []},
        "plugins": [],
        "capabilities": [
            {"id": "graph", "label": "Graph", "enabled": True},
            {"id": "tables", "label": "Tables", "enabled": True},
            {"id": "metricsDashboard", "label": "Metrics dashboard", "enabled": True},
            {"id": "diagnostics", "label": "Diagnostics", "enabled": False},
        ],
        "pages": [
            {"id": "snapshot", "label": "Snapshot", "kind": "snapshot",
             "required_capabilities": ["graph", "tables"], "default_visible": True},
            {"id": "dashboard", "label": "Dashboard", "kind": "dashboard",
             "required_capabilities": ["metricsDashboard"], "default_visible": True},
            {"id": "tables", "label": "Tables", "kind": "tables",
             "required_capabilities": ["tables"], "default_visible": True},
        ],
        "entity_kinds": [
            {"id": PYTHON_MODULE_KIND, "label": "Python module"},
            {"id": PYTHON_FILE_KIND, "label": "Python file"},
        ],
        "metrics": metrics,
        "relation_types": relation_types,
        "line_categories": line_categories,
        "visual_encodings": [],
        "graph_lenses": graph_lenses,
        "tables": tables,
        "queries": queries,
    }


def build_status_projection(
    *,
    project_id: str | None,
    branch: str | None,
    commit_count: int,
    store_present: bool,
    writer_active: bool,
) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "branch": branch,
        "commit_count": commit_count,
        "store_present": store_present,
        "writer_active": writer_active,
        "api_status": "experimental",
    }


def _json_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return str(isoformat())
    return str(value)


def build_commits_projection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "items": [
            {
                "commit_id": row.get("commit_hash", ""),
                "commit_order": row.get("commit_order", 0),
                "authored_at": _json_datetime(row.get("authored_at")),
                "summary": row.get("summary"),
            }
            for row in rows
        ],
    }


def build_entity_projection(
    *,
    entity_kind_id: str,
    commit_id: str | None,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    entities = [
        {
            "id": row.get("id") or row.get("module_name") or row.get("relative_path"),
            "kind": entity_kind_id,
            "label": row.get("label") or row.get("module_name") or row.get("relative_path"),
            "path": row.get("relative_path") or row.get("module_name"),
        }
        for row in rows
    ]
    return {"entity_kind_id": entity_kind_id, "commit_id": commit_id, "items": entities}


def build_graph_projection(
    *,
    commit_id: str,
    lens_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    nodes = [
        {
            "entity": {
                "id": n.get("module_name", ""),
                "kind": PYTHON_MODULE_KIND,
                "label": n.get("module_name", ""),
            },
            "metrics": [
                {"metric_id": k, "value": float(v), "aggregation": None}
                for k, v in (n.get("metrics") or {}).items()
            ],
            "line_counts": n.get("line_counts", {}),
        }
        for n in data.get("nodes", [])
    ]
    edges = [
        {
            "id": f"{e.get('source', '')}->{e.get('target', '')}",
            "source": {"id": e.get("source", ""), "kind": PYTHON_MODULE_KIND,
                       "label": e.get("source", "")},
            "target": {"id": e.get("target", ""), "kind": PYTHON_MODULE_KIND,
                       "label": e.get("target", "")},
            "relation_type_id": next(iter((e.get("kinds") or {}).keys()), "imports"),
            "metrics": [{"metric_id": "score", "value": float(e.get("score", 0)),
                         "aggregation": None}],
        }
        for e in data.get("edges", [])
    ]
    return {
        "commit_id": commit_id,
        "lens_id": lens_id,
        "nodes": nodes,
        "edges": edges,
        "metrics": [],
        "relation_types": [],
    }


def build_tables_index_projection() -> dict[str, Any]:
    return {
        "items": [
            {"id": _TABLE_MODULES_ID, "label": "Modules"},
            {"id": _TABLE_FILES_ID, "label": "Files"},
            {"id": _TABLE_RELATIONS_ID, "label": "Relations"},
        ],
    }


def build_table_modules_projection(
    *, commit_id: str | None, data: dict[str, Any],
) -> dict[str, Any]:
    columns = [
        {"id": "module_name", "label": "Module", "value_type": "string",
         "sortable": True, "visible_by_default": True, "align": "left"},
        {"id": "total_lines", "label": "Lines", "value_type": "number",
         "sortable": True, "visible_by_default": True, "align": "right"},
    ]
    rows = [
        {
            "id": str(r.get("module_name", "")),
            "cells": r,
            "actions": [{
                "id": "drilldown", "label": "Open files", "kind": "drilldown",
                "target_table_id": _TABLE_FILES_ID,
                "params": {"parentEntityId": r.get("module_name")},
            }],
        }
        for r in data.get("rows", [])
    ]
    return {
        "table_id": _TABLE_MODULES_ID, "title": "Modules", "commit_id": commit_id,
        "columns": columns, "rows": rows,
    }


def build_table_files_projection(
    *, commit_id: str | None, parent_entity_id: str | None, data: dict[str, Any],
) -> dict[str, Any]:
    rows_in = data.get("rows", [])
    columns = [
        {"id": "relative_path", "label": "File", "value_type": "string",
         "sortable": True, "visible_by_default": True, "align": "left"},
    ]
    line_category_by_id = {c.id: c for c in metric_catalog.line_categories()}
    metric_by_id = {m.metric_id: m for m in metric_catalog.all_metrics()}
    line_count_keys = _ordered_keys(
        (r.get("line_counts") or {}).keys()
        for r in rows_in
    )
    metric_keys = _ordered_keys(
        (r.get("metrics") or {}).keys()
        for r in rows_in
    )
    for key in line_count_keys:
        cat = line_category_by_id.get(key)
        metric = metric_by_id.get(key)
        columns.append({
            "id": f"line_counts.{key}",
            "label": cat.label if cat else metric.label if metric else _fallback_label(key),
            "value_type": "number",
            "sortable": True,
            "visible_by_default": bool(cat.default_enabled) if cat else key == "lines",
            "align": "right",
        })
    for key in metric_keys:
        columns.append({
            "id": f"metrics.{key}",
            "label": _metric_value_label(key, metric_by_id),
            "value_type": "number",
            "sortable": True,
            "visible_by_default": True,
            "align": "right",
        })
    rows = [
        {"id": f"{parent_entity_id or ''}/{r.get('relative_path', '')}",
         "cells": r, "actions": []}
        for r in rows_in
    ]
    return {
        "table_id": _TABLE_FILES_ID, "title": "Files", "commit_id": commit_id,
        "columns": columns, "rows": rows,
    }


def _ordered_keys(groups) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for key in group:
            if key in seen:
                continue
            seen.add(key)
            out.append(str(key))
    return out


def _metric_value_label(metric_key: str, metric_by_id: dict[str, Any]) -> str:
    for suffix in ("_mean", "_median", "_p95", "_max"):
        if metric_key.endswith(suffix):
            base = metric_key.removesuffix(suffix)
            metric = metric_by_id.get(base)
            if metric:
                return f"{metric.label} {_fallback_label(suffix.removeprefix('_'))}"
    metric = metric_by_id.get(metric_key)
    return metric.label if metric else _fallback_label(metric_key)


def _fallback_label(value: str) -> str:
    return value.replace("_", " ").replace(".", " ").title()


def build_table_relations_projection(
    *, commit_id: str | None, rows_in: list[dict[str, Any]],
) -> dict[str, Any]:
    relations = [
        {
            "source_id": r.get("source_id", ""),
            "target_id": r.get("target_id", ""),
            "relation_type_id": r.get("relation_type_id", ""),
            "strength": r.get("strength_value", 0),
        }
        for r in rows_in
    ]
    columns = [
        {"id": "source_id", "label": "Source", "value_type": "entity",
         "sortable": True, "visible_by_default": True},
        {"id": "target_id", "label": "Target", "value_type": "entity",
         "sortable": True, "visible_by_default": True},
        {"id": "relation_type_id", "label": "Type", "value_type": "string",
         "sortable": True, "visible_by_default": True},
        {"id": "strength", "label": "Strength", "value_type": "number",
         "sortable": True, "visible_by_default": True, "align": "right"},
    ]
    rows = [
        {
            "id": f"{rel['source_id']}->{rel['target_id']}:{rel['relation_type_id']}",
            "cells": rel, "actions": [],
        }
        for rel in relations
    ]
    return {
        "table_id": _TABLE_RELATIONS_ID, "title": "Relations",
        "commit_id": commit_id, "columns": columns, "rows": rows,
    }


def build_timeseries_projection(
    *, entity_kind_id: str, metric_id: str, aggregation: str,
    target_id: str | None, level: str, points: list[dict[str, Any]],
) -> dict[str, Any]:
    series = [
        {
            "label": target_id or level,
            "points": [
                {"commit_order": p.get("commit_order", 0),
                 "commit_id": p.get("commit_hash", ""),
                 "value": p.get("value")}
                for p in points
            ],
        }
    ]
    return {
        "entity_kind_id": entity_kind_id,
        "metric_id": metric_id,
        "aggregation": aggregation,
        "target_id": target_id,
        "series": series,
    }


def build_hotspots_projection(
    *, entity_kind_id: str, metric_id: str, aggregation: str,
    rank_by: str, items_raw: list[dict[str, Any]],
) -> dict[str, Any]:
    items = [
        {
            "entity": {
                "id": it.get("name", ""),
                "kind": entity_kind_id,
                "label": it.get("name", ""),
            },
            "current": it.get("current", 0),
            "first": it.get("first"),
            "growth": it.get("growth"),
        }
        for it in items_raw
    ]
    return {
        "entity_kind_id": entity_kind_id,
        "metric_id": metric_id,
        "aggregation": aggregation,
        "rank_by": rank_by,
        "items": items,
    }


TABLE_MODULES_ID: str = _TABLE_MODULES_ID
TABLE_FILES_ID: str = _TABLE_FILES_ID
TABLE_RELATIONS_ID: str = _TABLE_RELATIONS_ID

__all__ = [
    "TABLE_MODULES_ID",
    "TABLE_FILES_ID",
    "TABLE_RELATIONS_ID",
    "build_ui_config_projection",
    "build_status_projection",
    "build_commits_projection",
    "build_entity_projection",
    "build_graph_projection",
    "build_tables_index_projection",
    "build_table_modules_projection",
    "build_table_files_projection",
    "build_table_relations_projection",
    "build_timeseries_projection",
    "build_hotspots_projection",
]
