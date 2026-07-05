from __future__ import annotations

from pathlib import Path
from typing import Any

from ppi.query.dispatch import QueryMethod, dispatch

ALLOWED_QUERY_NAMES = frozenset(m.value for m in QueryMethod)


def _ensure_plain(obj: Any) -> Any:
    return obj.model_dump(mode="json") if hasattr(obj, "model_dump") else obj


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
                "error_code": "UNKNOWN_QUERY",
                "message": f"Unknown query: {query_name}",
                "details": {"query_name": query_name, "allowed": sorted(ALLOWED_QUERY_NAMES)},
            }

        if not self._store_path.is_file():
            return {
                "error_code": "STORAGE_UNAVAILABLE",
                "message": "Store not found. Run analysis first.",
                "details": {"store_path": str(self._store_path)},
            }

        try:
            result = dispatch(self._store_path, query_name, parameters or {})
        except Exception as exc:
            return {
                "error_code": "QUERY_FAILED",
                "message": str(exc),
                "details": {"query_name": query_name},
            }

        if result.is_error():
            return {
                "error_code": "QUERY_FAILED",
                "message": result.error.message if hasattr(result.error, 'message') else str(result.error),
                "details": {"query_name": query_name},
            }

        data = result.ok
        return self._normalize(data, limit)

    def _normalize(self, data: Any, limit: int | None = None) -> dict[str, Any]:
        data = _ensure_plain(data)
        columns: list[str] = []
        rows: list[dict[str, Any]] = []
        truncated = False

        if isinstance(data, dict):
            columns = list(data.keys())
            rows = [data]
        elif isinstance(data, list):
            columns = list(data[0].keys()) if data and isinstance(data[0], dict) else []
            if not data:
                return {"columns": [], "rows": [], "row_count": 0, "truncated": False}
            rows = [_ensure_plain(r) for r in data]
            if rows and isinstance(rows[0], dict):
                columns = list(rows[0].keys())
        else:
            rows = [{"value": data}]
            columns = ["value"]

        if limit is not None and len(rows) > limit:
            rows = rows[:limit]
            truncated = True

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
        }
