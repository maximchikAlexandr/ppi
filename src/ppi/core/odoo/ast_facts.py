"""Typed AST facts replacing tuple records in ``ClassSummary``.

The legacy ``ClassSummary`` stored facts as positional tuples like
``list[tuple[str, int]]`` and ``list[tuple[str, str, int, str]]``, which made
every reader index-dependent and error-prone. This module defines immutable
named value objects for each fact kind so fields are self-documenting.

Builders may hold mutable lists of these facts internally, but public snapshots
expose tuples.
"""

from __future__ import annotations

from dataclasses import dataclass

from ppi.core.value_objects import ContractError, EdgeKind, ModelName, SourceLine

__all__ = [
    "InheritLink",
    "FieldLink",
    "DecoratorPath",
    "EnvAccess",
    "MethodCallFact",
    "FieldPropertyAccessFact",
]


@dataclass(frozen=True, slots=True)
class InheritLink:
    """One ``_inherit`` reference to a model with its source line."""

    model: ModelName
    line: SourceLine | None


@dataclass(frozen=True, slots=True)
class FieldLink:
    """One relational field linking to a comodel (typed edge kind)."""

    kind: EdgeKind
    comodel: ModelName
    line: SourceLine | None
    detail: str


@dataclass(frozen=True, slots=True)
class DecoratorPath:
    """One field path inside an ``@api.depends``/``onchange``/``constrains`` decorator.

    ``decorator`` is one of ``"depends"``, ``"onchange"``, ``"constrains"``.
    """

    field_path: str
    line: SourceLine | None
    method_name: str
    decorator: str

    def __post_init__(self) -> None:
        if self.decorator not in ("depends", "onchange", "constrains"):
            raise ContractError(
                f"DecoratorPath.decorator must be depends/onchange/constrains, "
                f"got {self.decorator!r}"
            )


@dataclass(frozen=True, slots=True)
class EnvAccess:
    """One ``self.env['model']`` access inside a method."""

    model: ModelName
    line: SourceLine | None


@dataclass(frozen=True, slots=True)
class MethodCallFact:
    """One method call on a model recordset inside a method."""

    model: ModelName
    method: str
    line: SourceLine | None


@dataclass(frozen=True, slots=True)
class FieldPropertyAccessFact:
    """One field/property access on a model recordset inside a method."""

    model: ModelName
    field: str
    line: SourceLine | None


def edge_kind_for_relational_field(field_type: str) -> EdgeKind | None:
    """Map a relational field type name (e.g. ``Many2one``) to a typed edge kind."""
    match field_type:
        case "Many2one":
            return EdgeKind.PYTHON_MANY2ONE
        case "One2many":
            return EdgeKind.PYTHON_ONE2MANY
        case "Many2many":
            return EdgeKind.PYTHON_MANY2MANY
        case _:
            return None
