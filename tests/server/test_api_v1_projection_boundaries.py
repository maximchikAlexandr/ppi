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