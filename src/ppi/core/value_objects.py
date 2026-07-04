"""Domain value objects with fail-fast invariant contracts.

Each value object guards its own invariant through a factory ``of(...)`` or a
``__post_init__`` hook backed by :mod:`deal` preconditions. Programmer/system
invalid input raises :class:`ContractError` (fail-fast); recoverable user
errors are surfaced elsewhere via typed ``Result``/``NonFatalAnalysisFailure``.

String conversion and ``int`` packing are allowed only at serialization/UI
boundaries; inside the domain these types replace bare ``str``/``int`` where
the value has subject meaning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

import deal

__all__ = [
    "ContractError",
    "CommitHash",
    "ModuleName",
    "ModelName",
    "FieldName",
    "MethodName",
    "RelativeFilePath",
    "AbsolutePathText",
    "SourceLine",
    "LineCategory",
    "EdgeKind",
    "EdgeKindGroup",
    "line_category_of",
    "edge_kind_of",
    "edge_kind_group_of",
]


class ContractError(ValueError):
    """Fail-fast invariant/precondition violation in a value object.

    Distinct from plain ``ValueError`` so transport/CLI layers can tell a
    programmer/contract bug from a recoverable user error.
    """


# ponytail: contract style (F5/F6). Invariants via @deal.inv, preconditions
# via @deal.pre on factory methods, both raise ContractError. __post_init__
# only where no factory exists (deal.inv does not fire on __init__).
_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
_MODULE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MODEL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


def _positive_int(obj: object) -> bool:
    return (
        isinstance(obj.value, int)  # type: ignore[union-attr]
        and not isinstance(obj.value, bool)  # type: ignore[union-attr]
        and obj.value > 0
    )


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and _HEX_RE.match(obj.value),
    message="value must be a non-empty hex string",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class CommitHash:
    """Git commit hash (short or long, hex only)."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and _HEX_RE.match(value),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a commit hash value object from a hex string."""
        return cls(value)

    @classmethod
    def parse(cls, value: str) -> Self | None:
        """Parse a commit hash, returning ``None`` on malformed input."""
        if isinstance(value, str) and _HEX_RE.match(value) and value != "":
            return cls(value)
        return None

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and _MODULE_NAME_RE.match(obj.value),
    message="value must be a non-empty module-name identifier",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class ModuleName:
    """Odoo/Python module name (identifier-like)."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and _MODULE_NAME_RE.match(value),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a module name value object."""
        return cls(value)

    @classmethod
    def parse(cls, value: str) -> Self | None:
        """Parse a module name, returning ``None`` on malformed input."""
        if isinstance(value, str) and _MODULE_NAME_RE.match(value):
            return cls(value)
        return None

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and _MODEL_NAME_RE.match(obj.value),
    message="value must be a non-empty dot-separated model name",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class ModelName:
    """Odoo model name (dot-separated identifier, e.g. ``sale.order``)."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and _MODEL_NAME_RE.match(value),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a model name value object."""
        return cls(value)

    @classmethod
    def parse(cls, value: str) -> Self | None:
        """Parse a model name, returning ``None`` on malformed input."""
        if isinstance(value, str) and _MODEL_NAME_RE.match(value):
            return cls(value)
        return None

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and _MODULE_NAME_RE.match(obj.value),
    message="value must be a non-empty identifier",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class FieldName:
    """Odoo field name (identifier-like)."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and _MODULE_NAME_RE.match(value),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a field name value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and _MODULE_NAME_RE.match(obj.value),
    message="value must be a non-empty identifier",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class MethodName:
    """Python method name (identifier-like, may start with ``_``)."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and _MODULE_NAME_RE.match(value),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a method name value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and "\\" not in obj.value,
    message="value must be a non-empty posix path string",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class RelativeFilePath:
    """Module-relative file path, posix-style, no leading slash, no escaping.

    For adapter callers that still carry absolute filesystem paths (the Odoo
    pipeline accumulators store ``Path.as_posix()`` of an absolute path), use
    :meth:`coerce` which accepts both relative and absolute posix paths.
    """

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: (
            isinstance(value, str)
            and value != ""
            and "\\" not in value
            and not value.startswith("/")
        ),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build a relative file path value object (rejects absolute paths)."""
        return cls(value)

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and "\\" not in value,
        exception=ContractError,
    )
    def coerce(cls, value: str) -> Self:
        """Build a file path value object accepting absolute or relative posix.

        Used at the pipeline boundary where accumulator evidence still carries
        absolute paths; the invariant only rejects backslashes/empty.
        """
        return cls(value)

    def __str__(self) -> str:
        return self.value


@deal.inv(
    lambda obj: isinstance(obj.value, str) and obj.value != "" and obj.value.startswith("/"),
    message="value must be a non-empty absolute path starting with /",
    exception=ContractError,
)
@dataclass(frozen=True, slots=True)
class AbsolutePathText:
    """Absolute filesystem path stored as text (validated on adapter layer)."""

    value: str

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, str) and value != "" and value.startswith("/"),
        exception=ContractError,
    )
    def of(cls, value: str) -> Self:
        """Build an absolute path text value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


@deal.inv(_positive_int, message="value must be a positive int (>0)", exception=ContractError)
@dataclass(frozen=True, slots=True)
class SourceLine:
    """1-based source line number (``> 0``), or use ``None`` when unknown."""

    value: int

    @classmethod
    @deal.pre(
        lambda cls, value: isinstance(value, int) and not isinstance(value, bool) and value > 0,
        exception=ContractError,
    )
    def of(cls, value: int) -> Self:
        """Build a source line value object."""
        return cls(value)

    @classmethod
    def or_none(cls, value: int) -> Self | None:
        """Build a source line, returning ``None`` when ``value <= 0``."""
        return cls(value) if value > 0 else None

    def __int__(self) -> int:
        return self.value


class LineCategory(StrEnum):
    """Line-count categories tracked per module.

    Members are string enums so serialization to the storage/JSON boundary is
    a direct ``member.value`` without a mapping table.
    """

    PYTHON = "python_lines"
    JS = "js_lines"
    PYTHON_TEST = "python_test_lines"
    XML = "xml_lines"
    CSS = "css_lines"
    HTML = "html_lines"


def line_category_of(value: str) -> LineCategory | None:
    """Parse a line-category string into a typed member, ``None`` if unknown."""
    try:
        return LineCategory(value)
    except ValueError:
        return None


class EdgeKind(StrEnum):
    """All coupling edge kinds emitted by Python/XML/security analysis.

    String enums keep serialization stable; the kind is never an arbitrary
    string inside the domain.
    """

    PYTHON_MANY2ONE = "python_many2one"
    PYTHON_ONE2MANY = "python_one2many"
    PYTHON_MANY2MANY = "python_many2many"
    PYTHON_RELATED = "python_related"
    PYTHON_API_DEPENDS = "python_api_depends"
    PYTHON_API_ONCHANGE = "python_api_onchange"
    PYTHON_API_CONSTRAINS = "python_api_constrains"
    PYTHON_ENV_MODEL = "python_env_model"
    PYTHON_FIELD_PROPERTY_ACCESS = "python_field_property_access"
    PYTHON_INHERIT = "python__inherit"
    PYTHON_METHOD_CALL = "python_method_call"
    PYTHON_PRIVATE_METHOD_CALL = "python_private_method_call"
    XML_INHERIT_ID = "xml_inherit_id"
    XML_REF = "xml_ref"
    XML_PERCENT_REF = "xml_percent_ref"
    SECURITY_IR_RULE_REF = "security_ir_rule_ref"
    SECURITY_IR_RULE_MODEL_REF = "security_ir_rule_model_ref"
    SECURITY_XML_REF = "security_xml_ref"
    SECURITY_CSV_REF = "security_csv_ref"
    MANIFEST_DEPENDS = "manifest_depends"


def edge_kind_of(value: str) -> EdgeKind | None:
    """Parse an edge-kind string into a typed member, ``None`` if unknown."""
    try:
        return EdgeKind(value)
    except ValueError:
        return None


class EdgeKindGroup(StrEnum):
    """Graph-point breakdown group for an :class:`EdgeKind`."""

    MODEL_REUSE = "model_reuse"
    EXTENSION_OR_METHOD = "extension_or_method"
    VIEW = "view"
    FIELD_PROPERTY = "field_property"


_EDGE_KIND_TO_GROUP: dict[EdgeKind, EdgeKindGroup] = {
    EdgeKind.PYTHON_MANY2ONE: EdgeKindGroup.MODEL_REUSE,
    EdgeKind.PYTHON_ONE2MANY: EdgeKindGroup.MODEL_REUSE,
    EdgeKind.PYTHON_MANY2MANY: EdgeKindGroup.MODEL_REUSE,
    EdgeKind.PYTHON_RELATED: EdgeKindGroup.MODEL_REUSE,
    EdgeKind.PYTHON_API_DEPENDS: EdgeKindGroup.MODEL_REUSE,
    EdgeKind.PYTHON_API_ONCHANGE: EdgeKindGroup.MODEL_REUSE,
    EdgeKind.PYTHON_API_CONSTRAINS: EdgeKindGroup.MODEL_REUSE,
    EdgeKind.PYTHON_ENV_MODEL: EdgeKindGroup.MODEL_REUSE,
    EdgeKind.SECURITY_IR_RULE_MODEL_REF: EdgeKindGroup.MODEL_REUSE,
    EdgeKind.PYTHON_FIELD_PROPERTY_ACCESS: EdgeKindGroup.FIELD_PROPERTY,
    EdgeKind.PYTHON_INHERIT: EdgeKindGroup.EXTENSION_OR_METHOD,
    EdgeKind.PYTHON_METHOD_CALL: EdgeKindGroup.EXTENSION_OR_METHOD,
    EdgeKind.PYTHON_PRIVATE_METHOD_CALL: EdgeKindGroup.EXTENSION_OR_METHOD,
    EdgeKind.XML_INHERIT_ID: EdgeKindGroup.VIEW,
    EdgeKind.XML_REF: EdgeKindGroup.VIEW,
    EdgeKind.XML_PERCENT_REF: EdgeKindGroup.VIEW,
    EdgeKind.SECURITY_IR_RULE_REF: EdgeKindGroup.VIEW,
    EdgeKind.SECURITY_XML_REF: EdgeKindGroup.VIEW,
    EdgeKind.SECURITY_CSV_REF: EdgeKindGroup.VIEW,
    EdgeKind.MANIFEST_DEPENDS: EdgeKindGroup.EXTENSION_OR_METHOD,
}


def edge_kind_group_of(kind: EdgeKind) -> EdgeKindGroup:
    """Return the graph-point group for a typed edge kind.

    Raises :class:`ContractError` if the kind has no group mapping (bug).
    """
    group = _EDGE_KIND_TO_GROUP.get(kind)
    if group is None:
        raise ContractError(f"EdgeKind {kind!r} has no group mapping")
    return group
