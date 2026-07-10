"""Projection boundary: /api/v1 router is thin; shaping lives in projections.py."""

from __future__ import annotations

import inspect
import re

from ppi.server import api_v1
from ppi.query import projections


def test_api_v1_handlers_are_thin() -> None:
    """Each router handler must be a thin adapter: no row shaping inline.

    Row shaping (``row.get("camelKey") ...`` dict construction) belongs
    in projections.py. The router only extracts params, resolves commits,
    calls one projection and returns. We assert no camelCase string
    literal keys appear in the router — those live behind the CamelModel
    alias generator.
    """
    camel_keys_re = re.compile(r'"[a-z]+[A-Z][a-zA-Z]*"\s*:')
    for name in (
        "get_status_v1", "get_ui_config_v1", "list_commits_v1", "list_entities_v1",
        "get_graph_v1", "list_tables_v1", "get_table_v1",
        "get_metric_timeseries_v1", "get_metric_hotspots_v1",
    ):
        fn = getattr(api_v1, name)
        src = inspect.getsource(fn)
        assert not re.search(r"^\s*import\s+ppi\.", src, flags=re.MULTILINE), (
            f"{name} contains an inline import"
        )
        assert not re.search(r"^\s*(import|from)\s+", src, flags=re.MULTILINE), (
            f"{name} contains an inline import"
        )
        assert not camel_keys_re.search(src), (
            f"{name} contains inline camelCase string literals; "
            "shaping must live in projections.py with snake_case keys"
        )


def test_projections_module_owns_shaping() -> None:
    src = inspect.getsource(projections)
    assert "build_graph_projection" in src
    assert "build_table_projection" not in src or "build_table_modules_projection" in src
    assert "build_entity_projection" in src
    assert "build_commits_projection" in src
    assert "build_timeseries_projection" in src
    assert "build_hotspots_projection" in src
    assert "build_ui_config_projection" in src


def test_commit_projection_serializes_datetime_like_authored_at() -> None:
    class TimestampLike:
        def isoformat(self) -> str:
            return "2026-07-10T11:13:00"

    out = projections.build_commits_projection([
        {
            "commit_hash": "abc",
            "commit_order": 1,
            "authored_at": TimestampLike(),
            "summary": "demo",
        }
    ])

    assert out["items"][0]["authored_at"] == "2026-07-10T11:13:00"


def test_file_table_projection_exposes_line_counts_and_metrics() -> None:
    out = projections.build_table_files_projection(
        commit_id="c",
        parent_entity_id="mod",
        data={
            "rows": [
                {
                    "relative_path": "models/a.py",
                    "line_counts": {"lines": 42, "function_count": 3},
                    "metrics": {"cyclomatic_mean": 4.5},
                }
            ]
        },
    )

    column_ids = [c["id"] for c in out["columns"]]
    assert "line_counts.lines" in column_ids
    assert "line_counts.function_count" in column_ids
    assert "metrics.cyclomatic_mean" in column_ids
