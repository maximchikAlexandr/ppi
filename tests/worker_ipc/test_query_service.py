from pathlib import Path

import pytest

from ppi.worker_ipc.query_service import ALLOWED_QUERY_NAMES, QueryService


def test_allowed_query_names_from_enum() -> None:
    from ppi.query.dispatch import QueryMethod
    expected = frozenset(m.value for m in QueryMethod)
    assert ALLOWED_QUERY_NAMES == expected
    assert "commits" in ALLOWED_QUERY_NAMES
    assert "snapshot/table/modules" in ALLOWED_QUERY_NAMES
    assert "catalog" not in ALLOWED_QUERY_NAMES
    assert "snapshot/modules" not in ALLOWED_QUERY_NAMES


@pytest.mark.asyncio
async def test_unknown_query(tmp_path: Path) -> None:
    service = QueryService(tmp_path / "store.duckdb")
    result = await service.execute("nonexistent")
    assert result.get("error_code") == "UNKNOWN_QUERY"


@pytest.mark.asyncio
async def test_unknown_legacy_names(tmp_path: Path) -> None:
    service = QueryService(tmp_path / "store.duckdb")
    for name in ["catalog", "snapshot/modules", "raw/sql"]:
        result = await service.execute(name)
        assert result.get("error_code") == "UNKNOWN_QUERY", f"{name} should be unknown"


@pytest.mark.asyncio
async def test_store_missing(tmp_path: Path) -> None:
    service = QueryService(tmp_path / "nonexistent.duckdb")
    result = await service.execute("commits")
    assert result.get("error_code") == "STORAGE_UNAVAILABLE"


def test_dict_normalization(tmp_path: Path) -> None:
    service = QueryService(tmp_path / "store.duckdb")
    result = service._normalize({"key": "value", "count": 42})
    assert result["columns"] == ["key", "count"]
    assert result["row_count"] == 1
    assert result["truncated"] is False


def test_list_normalization(tmp_path: Path) -> None:
    service = QueryService(tmp_path / "store.duckdb")
    result = service._normalize([{"a": 1}, {"a": 2}])
    assert result["columns"] == ["a"]
    assert result["row_count"] == 2
    assert result["truncated"] is False


def test_scalar_normalization(tmp_path: Path) -> None:
    service = QueryService(tmp_path / "store.duckdb")
    result = service._normalize(42)
    assert result["columns"] == ["value"]
    assert result["row_count"] == 1
    assert result["rows"] == [{"value": 42}]


def test_limit_truncation(tmp_path: Path) -> None:
    service = QueryService(tmp_path / "store.duckdb")
    result = service._normalize([{"a": i} for i in range(10)], limit=3)
    assert result["row_count"] == 3
    assert result["truncated"] is True
