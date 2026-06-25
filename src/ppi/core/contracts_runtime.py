"""Runtime precondition/invariant contract helpers.

Two categories of error live in this codebase:

* **Recoverable user/environment error** -> returned as a typed ``Result`` or
  ``NonFatalAnalysisFailure`` (see :mod:`ppi.core.errors`).
* **Programmer/system invariant violation** -> fail-fast exception raised by
  these helpers (:class:`ContractError`).

This module is the only place in the domain that raises for contract
violations via plain function helpers. Value-object invariants are declared
via ``@deal.inv``/``@deal.pre`` in :mod:`ppi.core.value_objects`; these
function helpers cover pure-function preconditions that are not attached to a
value object constructor.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from ppi.core.value_objects import ContractError

__all__ = [
    "ContractError",
    "require",
    "ensure",
    "check",
    "require_non_empty",
    "require_non_empty_collection",
    "require_non_negative",
    "require_positive",
    "require_in_range",
]

T = TypeVar("T")


def require(predicate: bool, message: str) -> None:
    """Fail-fast precondition: raise :class:`ContractError` if ``predicate`` is false."""
    if not predicate:
        raise ContractError(message)


def ensure(predicate: bool, message: str) -> None:
    """Fail-fast postcondition: raise :class:`ContractError` if ``predicate`` is false."""
    if not predicate:
        raise ContractError(f"postcondition violated: {message}")


def check(predicate: bool, message: str) -> None:
    """Fail-fast invariant check alias used inside value object factories."""
    if not predicate:
        raise ContractError(f"invariant violated: {message}")


def require_non_empty(value: str, label: str = "value") -> str:
    """Precondition: value is a non-empty string."""
    if not isinstance(value, str) or value == "":
        raise ContractError(f"{label} must be a non-empty string, got {value!r}")
    return value


def require_non_empty_collection(value: Iterable[T], label: str = "collection") -> Iterable[T]:
    """Precondition: iterable yields at least one element."""
    items = list(value)
    if not items:
        raise ContractError(f"{label} must be non-empty")
    return items


def require_non_negative(value: int, label: str = "value") -> int:
    """Precondition: integer >= 0."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ContractError(f"{label} must be a non-negative int, got {value!r}")
    return value


def require_positive(value: int, label: str = "value") -> int:
    """Precondition: integer > 0."""
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ContractError(f"{label} must be a positive int (>0), got {value!r}")
    return value


def require_in_range(
    value: int | float,
    low: int | float,
    high: int | float,
    label: str = "value",
) -> int | float:
    """Precondition: ``low <= value <= high``."""
    if not (low <= value <= high):
        raise ContractError(f"{label} must be in {low}..{high}, got {value}")
    return value


# ponytail: the ``pre = deal.pre`` / ``ensure_deal = deal.ensure`` / ``inv =
# deal.inv`` aliases were removed (F6) — they duplicated deal's own API under
# a second name without a second caller. Use ``deal.pre``/``deal.inv`` directly
# (as value_objects.py now does). ``deal`` stays imported here for the
# introspection helpers if a caller wants them.
