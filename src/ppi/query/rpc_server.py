"""Read-only stdio JSON-RPC servant transport for ``ppi rpc``.

Routes queries through Ibis pipeline instead of legacy StoreReader.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import msgspec

from expression.core.result import Result

from ppi.query import dispatch
from ppi.query.contracts import RpcRequest
from ppi.runtime import lock as project_lock
from ppi.runtime.paths import store_path, writer_lock_path
from ppi.storage import schema


def _json_default(obj: object) -> object:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    raise TypeError(f"not serializable: {type(obj)!r}")


def serve_rpc(repo: Path) -> None:
    store_file = store_path(repo)
    lock_file = writer_lock_path(repo)

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = msgspec.json.decode(line.encode("utf-8"), type=RpcRequest)
        except msgspec.DecodeError:
            sys.stdout.write(
                json.dumps(
                    {"id": -1, "error": {"code": "INVALID_PARAMS", "message": "malformed request"}}
                ) + "\n"
            )
            sys.stdout.flush()
            continue
        if request.method == "rpc.close":
            break
        writer_active = project_lock.is_locked(lock_file)
        store_present = store_file.is_file()
        schema_error: schema.SchemaIncompatibleError | None = None
        if store_present and not writer_active:
            try:
                _check_schema(store_file)
            except schema.SchemaIncompatibleError as exc:
                schema_error = exc
            except OSError:
                pass
        try:
            result = dispatch(
                store_file if not schema_error and store_present else None,
                request.method,
                request.params,
                writer_active=writer_active,
                store_present=store_present,
                schema_error=schema_error,
            )
            match result:
                case Result(tag='ok', ok=value):
                    payload = {"id": request.id, "result": value}
                case Result(tag='error', error=err):
                    code = dict(err.details).get("code", err.code.value)
                    payload = {"id": request.id, "error": {"code": code, "message": err.message}}
            sys.stdout.write(
                json.dumps(payload, ensure_ascii=False, default=_json_default) + "\n"
            )
        except (TypeError, ValueError) as exc:
            sys.stdout.write(
                json.dumps(
                    {"id": request.id, "error": {"code": "INTERNAL", "message": f"serialization failed: {exc}"}},
                    ensure_ascii=False,
                ) + "\n"
            )
        sys.stdout.flush()


def _check_schema(store_file: Path) -> None:
    import duckdb
    try:
        conn = duckdb.connect(str(store_file), read_only=True)
        try:
            schema.assert_schema_compatible(conn)
        finally:
            conn.close()
    except schema.SchemaIncompatibleError:
        raise
    except Exception:
        pass


__all__ = ["serve_rpc"]
