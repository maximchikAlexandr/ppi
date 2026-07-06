import pytest

from ppi.worker_ipc.query_service import normalize_query_result


def test_normalize_scalar() -> None:
    result = normalize_query_result(42)
    assert result.columns == ("value",)
    assert result.rows == ({"value": 42},)
    assert result.row_count == 1
    assert result.truncated is False


def test_normalize_dict() -> None:
    data = {"a": 1, "b": 2}
    result = normalize_query_result(data)
    assert list(result.columns) == ["a", "b"]
    assert result.rows == ({"a": 1, "b": 2},)
    assert result.row_count == 1


def test_normalize_list_of_dicts() -> None:
    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    result = normalize_query_result(data)
    assert list(result.columns) == ["a", "b"]
    assert result.row_count == 2


def test_normalize_list_of_models() -> None:
    class Row:
        def __init__(self, a: int, b: int) -> None:
            self.a = a
            self.b = b

        def model_dump(self, mode: str = "python") -> dict[str, int]:
            return {"a": self.a, "b": self.b}

    data = [Row(1, 2), Row(3, 4)]
    result = normalize_query_result(data)
    assert list(result.columns) == ["a", "b"]
    assert result.row_count == 2


def test_normalize_empty_list() -> None:
    result = normalize_query_result([])
    assert result.columns == ()
    assert result.rows == ()
    assert result.row_count == 0


def test_normalize_truncation() -> None:
    data = [{"a": i} for i in range(10)]
    result = normalize_query_result(data, limit=3)
    assert result.row_count == 3
    assert result.truncated is True


def test_normalize_no_truncation_when_under_limit() -> None:
    data = [{"a": i} for i in range(3)]
    result = normalize_query_result(data, limit=10)
    assert result.row_count == 3
    assert result.truncated is False
