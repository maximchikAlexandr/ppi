"""Ibis DuckDB backend binding and table registry.

Provides:
- Ibis connection factory bound to a DuckDB store file.
- Table reference registry for the history store schema.
- Execution helper that converts backend errors to DomainError.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import ibis
import ibis.expr.types as ir

from ppi.core.errors import DomainError, ErrorCategory, ErrorCode
from ppi.core.result import Error, Ok, Result

_ibis_connections: dict[str, list[ibis.BaseBackend]] = {}
_query_lock = threading.Lock()


def connect_ibis(store_file: Path) -> Result[ibis.BaseBackend, DomainError]:
    try:
        con = ibis.duckdb.connect(str(store_file), read_only=True)
        _ibis_connections.setdefault(str(store_file), []).append(con)
        return Ok(con)
    except Exception as exc:
        return Error(
            DomainError(
                code=ErrorCode.STORAGE_ERROR,
                category=ErrorCategory.STORAGE,
                message=f"Failed to connect Ibis to store: {exc}",
                cause=exc if isinstance(exc, BaseException) else None,
            ),
        )


def disconnect_ibis(store_file: Path) -> None:
    key = str(store_file)
    connections = _ibis_connections.pop(key, [])
    for con in connections:
        try:
            con.disconnect()
        except Exception:
            pass


def disconnect_backend(backend: ibis.BaseBackend) -> None:
    for key, connections in list(_ibis_connections.items()):
        _ibis_connections[key] = [con for con in connections if con is not backend]
        if not _ibis_connections[key]:
            _ibis_connections.pop(key, None)
    try:
        backend.disconnect()
    except Exception:
        pass


def get_backend(store_file: Path) -> ibis.BaseBackend | None:
    connections = _ibis_connections.get(str(store_file), [])
    return connections[-1] if connections else None


def load_table(
    backend: ibis.BaseBackend,
    table_name: str,
) -> Result[ir.Table, DomainError]:
    try:
        table = backend.table(table_name)
        return Ok(table)
    except Exception as exc:
        return Error(
            DomainError(
                code=ErrorCode.QUERY_ERROR,
                category=ErrorCategory.QUERY,
                message=f"Failed to load table {table_name}: {exc}",
                stage="ibis_backend.load_table",
                cause=exc if isinstance(exc, BaseException) else None,
            ),
        )


def execute_expr(
    backend: ibis.BaseBackend,
    expr: ir.Table,
) -> Result[list[dict[str, Any]], DomainError]:
    try:
        with _query_lock:
            result = backend.execute(expr)
        records = (
            result.to_dict(orient="records")
            if hasattr(result, "to_dict")
            else result.to_dict("records")
        )
        return Ok(records)
    except Exception as exc:
        return Error(
            DomainError(
                code=ErrorCode.QUERY_ERROR,
                category=ErrorCategory.QUERY,
                message=f"Ibis execution failed: {exc}",
                stage="ibis_backend.execute_expr",
                cause=exc if isinstance(exc, BaseException) else None,
            ),
        )


def table_exists(backend: ibis.BaseBackend, table_name: str) -> bool:
    try:
        return table_name in backend.list_tables()
    except Exception:
        return False
