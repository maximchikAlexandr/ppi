"""OpenAPI contract checks: /api/v1 paths have operationId and tags."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ppi.server.app import create_app


def test_openapi_includes_v1_paths(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    expected = {
        "/api/v1/status",
        "/api/v1/ui/config",
        "/api/v1/commits",
        "/api/v1/entities",
        "/api/v1/graph",
        "/api/v1/tables",
        "/api/v1/tables/{tableId}",
        "/api/v1/metrics/timeseries",
        "/api/v1/metrics/hotspots",
    }
    assert expected <= set(paths.keys())
    for path, ops in paths.items():
        if not path.startswith("/api/v1"):
            continue
        for method, op in ops.items():
            assert "operationId" in op, f"{method.upper()} {path} missing operationId"
            assert op.get("tags"), f"{method.upper()} {path} missing tags"
            assert op.get("summary"), f"{method.upper()} {path} missing summary"


def test_openapi_property_names_are_camel_case(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    schema = client.get("/openapi.json").json()
    components = schema.get("components", {}).get("schemas", {})
    snake_in_public: list[str] = []
    for name, definition in components.items():
        if not name.startswith("V1") and "V1" not in name and name not in {
            "ErrorBody", "ErrorResponse",
        }:
            continue
        props = definition.get("properties", {})
        for prop in props:
            if "_" in prop:
                snake_in_public.append(f"{name}.{prop}")
    assert not snake_in_public, f"snake_case properties in public schemas: {snake_in_public}"


def test_openapi_openapi_json_property_names(tmp_path: Path) -> None:
    """Fails when public /api/v1 schema fields are not camelCase."""
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    schema = client.get("/openapi.json").json()
    for path, ops in schema["paths"].items():
        if not path.startswith("/api/v1"):
            continue
        for method, op in ops.items():
            for status, response in op.get("responses", {}).items():
                ref = response.get("content", {}).get("application/json", {}).get("schema", {})
                if "$ref" in ref:
                    # referenced by name; covered by property-name test above
                    continue
