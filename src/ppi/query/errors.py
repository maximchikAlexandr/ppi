"""Query-layer errors."""

from __future__ import annotations

__all__ = [
    "QueryError",
]


class QueryError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        http_status: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)

    def __repr__(self) -> str:
        return f"QueryError(code={self.code!r}, http_status={self.http_status})"
