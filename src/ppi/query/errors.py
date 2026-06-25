"""Typed query-layer errors (PPI-044).

Replaces the mutable ``QueryError(Exception)`` (which assigned ``self.code`` /
``self.message`` / ``self.http_status`` as mutable attributes) with a frozen
``QueryFailure`` value object plus a thin exception wrapper. The failure is a
domain value; the exception is only the unwind/transport mechanism.

``QueryError`` stays re-exported as a backwards-compatible wrapper so existing
callers (dispatch, rpc_server, api) keep working while they migrate to reading
``exc.failure``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import deal

from ppi.core.value_objects import ContractError

__all__ = [
    "QueryErrorCode",
    "QueryFailure",
    "QueryError",
    "raise_query_failure",
]


class QueryErrorCode(StrEnum):
    """Discriminator for query failure reasons."""

    INVALID_PARAMS = "INVALID_PARAMS"
    QUERY_NOT_FOUND = "QUERY_NOT_FOUND"
    METHOD_NOT_FOUND = "METHOD_NOT_FOUND"
    LOCKED = "LOCKED"
    SCHEMA_INCOMPATIBLE = "SCHEMA_INCOMPATIBLE"
    STORE_NOT_FOUND = "STORE_NOT_FOUND"
    INTERNAL = "INTERNAL"


@deal.inv(
    lambda obj: (
        isinstance(obj.code, QueryErrorCode)
        and isinstance(obj.message, str)
        and obj.message != ""
        and isinstance(obj.http_status, int)
        and not isinstance(obj.http_status, bool)
        and 400 <= obj.http_status <= 599
    ),
    message="QueryFailure invariant: code, non-empty message, http_status in 400..599",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class QueryFailure:
    """Immutable query failure value: code + message + HTTP status.

    ``http_status`` is constrained to the 400..599 client/server-error range.
    """

    code: QueryErrorCode
    message: str
    http_status: int = 400

    @classmethod
    @deal.pre(
        lambda cls, code, message, http_status=400: (
            isinstance(message, str)
            and message != ""
            and isinstance(http_status, int)
            and not isinstance(http_status, bool)
            and 400 <= http_status <= 599
        ),
        exception=ContractError,
    )
    def of(
        cls,
        code: QueryErrorCode | str,
        message: str,
        *,
        http_status: int = 400,
    ) -> QueryFailure:
        """Build a query failure, coercing a string code to the enum."""
        typed_code = code if isinstance(code, QueryErrorCode) else QueryErrorCode(code)
        return cls(code=typed_code, message=message, http_status=http_status)

    def raise_(self) -> None:
        """Raise this failure wrapped in a :class:`QueryError`."""
        raise QueryError(self)


class QueryError(Exception):
    """Thin exception wrapper carrying one frozen :class:`QueryFailure`.

    Backwards-compatible with legacy callers that construct it positionally
    as ``QueryError(code, message, *, http_status)`` and read ``.code``,
    ``.message``, ``.http_status`` — those properties delegate to the wrapped
    failure. Also accepts a single :class:`QueryFailure` for the typed path.
    """

    def __init__(
        self,
        failure_or_code: QueryFailure | QueryErrorCode | str,
        message: str | None = None,
        *,
        http_status: int = 400,
    ) -> None:
        if isinstance(failure_or_code, QueryFailure):
            self.failure = failure_or_code
        else:
            self.failure = QueryFailure.of(failure_or_code, message or "", http_status=http_status)
        super().__init__(self.failure.message)

    @property
    def code(self) -> str:
        """Return the failure code value (legacy compat)."""
        return self.failure.code.value

    @property
    def message(self) -> str:
        """Return the failure message (legacy compat)."""
        return self.failure.message

    @property
    def http_status(self) -> int:
        """Return the failure HTTP status (legacy compat)."""
        return self.failure.http_status

    def __repr__(self) -> str:
        return f"QueryError(code={self.code!r}, http_status={self.http_status})"


def raise_query_failure(
    code: QueryErrorCode | str,
    message: str,
    *,
    http_status: int = 400,
) -> None:
    """Build a :class:`QueryFailure` and raise it wrapped in :class:`QueryError`."""
    QueryFailure.of(code, message, http_status=http_status).raise_()
