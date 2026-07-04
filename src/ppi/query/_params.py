"""Parameter coercion helpers.

The ``_opt_*`` helpers coerce ``str|bool|int|float`` because ``params`` is
shape-polymorphic across transports (JSON bools from ``ppi rpc`` vs strings from
HTTP query strings).

``QueryError`` is re-exported from :mod:`ppi.query.errors` so there is a single
typed error class across the query layer (PPI-044).
"""

from __future__ import annotations

from ppi.query.errors import QueryError

__all__ = [
    "QueryError",
    "_opt_bool",
    "_opt_str",
    "_req",
]


def _req(params: dict, key: str) -> str:
    value = params.get(key)
    if not value:
        raise QueryError("INVALID_PARAMS", f"{key} is required", http_status=422)
    return str(value)


def _opt_str(params: dict, key: str) -> str | None:
    value = params.get(key)
    return str(value) if value not in (None, "") else None


def _opt_bool(params: dict, key: str, default: bool = False) -> bool:
    value = params.get(key)
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).lower() in {"1", "true", "yes", "on"}
