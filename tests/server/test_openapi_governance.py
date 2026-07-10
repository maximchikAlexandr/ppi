"""OpenAPI governance fixtures.

Fails when a public operation lacks operationId, or when public /api/v1
schema fields contain underscores. The diff script has its own
end-to-end test in the Makefile target `make api-diff`; the
historical "missing baseline" test was retired when the first
stable baseline was promoted.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ppi.server.app import create_app


def test_public_operation_requires_operation_id(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    schema = client.get("/openapi.json").json()
    for path, ops in schema["paths"].items():
        if not path.startswith("/api/v1"):
            continue
        for method, op in ops.items():
            assert "operationId" in op, f"{method.upper()} {path} has no operationId"


def test_public_schema_property_names_are_camel_case(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "missing.duckdb", tmp_path / "missing.lock"))
    schema = client.get("/openapi.json").json()
    components = schema.get("components", {}).get("schemas", {})
    public_schema_names = {
        "ErrorBody", "ErrorResponse", "StatusV1Response", "ListCommitsV1Response",
        "UiConfigV1Response", "EntityRefV1", "EntityTargetV1", "ListEntitiesV1Response",
        "GraphNodeV1", "GraphEdgeV1", "GraphV1Response", "TableColumnV1",
        "TableRowActionV1", "TableRowV1", "TableV1Response", "ListTablesV1Response",
        "MetricTimeseriesPointV1", "MetricTimeseriesSeriesV1", "MetricTimeseriesV1Response",
        "MetricHotspotsItemV1", "MetricHotspotsV1Response",
    }
    violations: list[str] = []
    for name, definition in components.items():
        if name not in public_schema_names:
            continue
        for prop in definition.get("properties", {}):
            if "_" in prop:
                violations.append(f"{name}.{prop}")
    assert not violations, f"snake_case properties in public schemas: {violations}"
