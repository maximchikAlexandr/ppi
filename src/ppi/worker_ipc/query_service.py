from __future__ import annotations

from pathlib import Path
from typing import Any

import msgspec

from ppi.query.dispatch import QueryMethod, dispatch
from ppi.worker_ipc.protocol import WorkerErrorCode

ALLOWED_QUERY_NAMES = frozenset(m.value for m in QueryMethod)


class QueryExecuteResult(msgspec.Struct, frozen=True, kw_only=True):
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    row_count: int
    truncated: bool


def _ensure_plain(obj: Any) -> Any:
    return obj.model_dump(mode="json") if hasattr(obj, "model_dump") else obj


def normalize_query_result(data: Any, *, limit: int | None = None) -> QueryExecuteResult:
    """Pure normalization of dispatch result into ``QueryExecuteResult``.

    No IO, no WorkerClient, no FastAPI/Click imports.
    """
    data = _ensure_plain(data)
    columns: list[str] = []
    rows: list[dict[str, Any]] = []
    truncated = False

    if isinstance(data, dict):
        columns = list(data.keys())
        rows = [data]
    elif isinstance(data, list):
        if not data:
            return QueryExecuteResult(columns=(), rows=(), row_count=0, truncated=False)
        rows = [_ensure_plain(r) for r in data]
        if rows and isinstance(rows[0], dict):
            columns = list(rows[0].keys())
    else:
        rows = [{"value": data}]
        columns = ["value"]

    if limit is not None and len(rows) > limit:
        rows = rows[:limit]
        truncated = True

    return QueryExecuteResult(
        columns=tuple(columns),
        rows=tuple(rows),
        row_count=len(rows),
        truncated=truncated,
    )


class QueryService:
    def __init__(self, store_path: Path) -> None:
        self._store_path = store_path

    async def execute(
        self,
        query_name: str,
        parameters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        if query_name not in ALLOWED_QUERY_NAMES:
            return {
                "error_code": WorkerErrorCode.UNKNOWN_QUERY.value,
                "message": f"Unknown query: {query_name}",
                "details": {"query_name": query_name, "allowed": sorted(ALLOWED_QUERY_NAMES)},
            }

        if not self._store_path.is_file():
            return {
                "error_code": WorkerErrorCode.STORAGE_UNAVAILABLE.value,
                "message": "Store not found. Run analysis first.",
                "details": {"store_path": str(self._store_path)},
            }

        try:
            result = dispatch(self._store_path, query_name, parameters or {})
        except Exception:
            return {
                "error_code": WorkerErrorCode.QUERY_FAILED.value,
                "message": "Query execution failed",
                "details": {"query_name": query_name},
            }

        if result.is_error():
            return {
                "error_code": WorkerErrorCode.QUERY_FAILED.value,
                "message": "Query execution failed",
                "details": {"query_name": query_name},
            }

        data = result.ok
        normalized = normalize_query_result(data, limit=limit)
        return {
            "columns": list(normalized.columns),
            "rows": list(normalized.rows),
            "row_count": normalized.row_count,
            "truncated": normalized.truncated,
        }
