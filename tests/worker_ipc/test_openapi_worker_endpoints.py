from pathlib import Path


def test_openapi_schema_includes_worker_with_client(tmp_path: Path) -> None:
    from ppi.server.app import openapi_schema
    schema = openapi_schema(
        store_file=tmp_path / "store.duckdb",
        lock_file=tmp_path / "writer.lock",
        worker_client=True,
    )
    paths = schema.get("paths", {})
    worker_paths = [p for p in paths if p.startswith("/api/worker")]
    assert len(worker_paths) >= 1, f"No /api/worker paths found in {list(paths.keys())}"
