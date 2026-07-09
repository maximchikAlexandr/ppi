"""Contract-shape enforcement: exported OpenAPI must match api-contract.md.

This is the teeth behind ``specs/010-frontend-api-platform/contracts/api-contract.md``:
the contract document is normative, and this test fails when the exported
OpenAPI drifts from the field names, wrappers, defaults and path param
naming the contract mandates. Without this, ``api-contract.md`` is a wish
list — drift already happened in 8 places before this test existed.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from ppi.server.app import create_app


def _schema(tmp_path: Path) -> dict:
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    return client.get("/openapi.json").json()


def _resolve(schema: dict, ref: str) -> dict:
    name = ref.split("/")[-1]
    return schema["components"]["schemas"][name]


def _response_schema(schema: dict, path: str, method: str = "get", status: str = "200") -> dict:
    op = schema["paths"][path][method]
    ref = op["responses"][status]["content"]["application/json"]["schema"]["$ref"]
    return _resolve(schema, ref)


def test_path_param_is_camel_case(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    assert "/api/v1/tables/{tableId}" in schema["paths"]
    assert "/api/v1/tables/{table_id}" not in schema["paths"]


def test_commits_uses_items_wrapper(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    resp = _response_schema(schema, "/api/v1/commits")
    assert "items" in resp["properties"]
    assert "commits" not in resp["properties"]


def test_entities_uses_items_wrapper(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    resp = _response_schema(schema, "/api/v1/entities")
    assert "items" in resp["properties"]
    assert "entities" not in resp["properties"]


def test_entities_limit_default_and_bounds(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    params = schema["paths"]["/api/v1/entities"]["get"]["parameters"]
    limit = next(p for p in params if p["name"] == "limit")
    assert limit["schema"]["default"] == 5000
    assert limit["schema"]["minimum"] == 1
    assert limit["schema"]["maximum"] == 10000


def test_tables_index_uses_items_wrapper(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    resp = _response_schema(schema, "/api/v1/tables")
    assert "items" in resp["properties"]
    assert "tables" not in resp["properties"]


def test_graph_lens_id_is_required(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    params = schema["paths"]["/api/v1/graph"]["get"]["parameters"]
    lens_id = next(p for p in params if p["name"] == "lensId")
    assert lens_id["required"] is True


def test_timeseries_series_uses_label_not_name(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    resp = _response_schema(schema, "/api/v1/metrics/timeseries")
    series_item = _resolve(schema, resp["properties"]["series"]["items"]["$ref"])
    assert "label" in series_item["properties"]
    assert "name" not in series_item["properties"]


def test_timeseries_has_target_id_field(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    resp = _response_schema(schema, "/api/v1/metrics/timeseries")
    assert "targetId" in resp["properties"]


def test_hotspots_item_uses_entity_ref(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    resp = _response_schema(schema, "/api/v1/metrics/hotspots")
    item = _resolve(schema, resp["properties"]["items"]["items"]["$ref"])
    assert "entity" in item["properties"]
    assert "entityId" not in item["properties"]


def test_hotspots_rank_by_is_required(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    params = schema["paths"]["/api/v1/metrics/hotspots"]["get"]["parameters"]
    rank_by = next(p for p in params if p["name"] == "rankBy")
    assert rank_by["required"] is True


def test_tables_path_has_limit_query(tmp_path: Path) -> None:
    schema = _schema(tmp_path)
    params = schema["paths"]["/api/v1/tables/{tableId}"]["get"]["parameters"]
    limit = next(p for p in params if p["name"] == "limit")
    assert limit["schema"]["default"] == 500
    assert limit["schema"]["minimum"] == 1
    assert limit["schema"]["maximum"] == 5000


def test_committed_openapi_matches_export(tmp_path: Path) -> None:
    """The committed openapi.json must match a fresh export from the app.

    This is the freshness guard in test form: if someone changes Pydantic
    schemas and forgets to regenerate+commit openapi.json, this fails.
    """
    repo = Path(__file__).resolve().parents[2]
    committed_path = repo / "openapi" / "openapi.json"
    if not committed_path.exists():
        return
    committed = json.loads(committed_path.read_text())
    fresh = _schema(tmp_path)
    assert committed["paths"] == fresh["paths"], "committed openapi.json paths drift from app export"
    assert committed["components"]["schemas"] == fresh["components"]["schemas"], (
        "committed openapi.json schemas drift from app export; run 'make api-contract' and commit"
    )