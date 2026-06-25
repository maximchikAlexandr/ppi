"""Odoo manifest domain model and pure parser.

Splits the old ``parse_manifest(path) -> dict[str, Any]`` into:

* :class:`Manifest` — immutable value object with ``depends`` as a frozenset of
  typed :class:`ModuleName`. Parse failures are not lost in a fallback ``{}``.
* :func:`parse_manifest_source` — pure function that takes already-read source
  text and returns ``Result[Manifest, ManifestParseFailed]``. File reading is
  out of scope here (adapter layer).
* :func:`manifest_from_literal` — pure function over an ``ast.literal_eval``
  result; the AST form lookup uses structural pattern matching.

A manifest that cannot be parsed returns a typed failure instead of raising
``ValueError`` or silently becoming an empty dict.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Self

from expression.core.result import Error, Ok, Result

from ppi.core.value_objects import ContractError, ModuleName

__all__ = [
    "Manifest",
    "ManifestParseFailed",
    "ManifestParseError",
    "parse_manifest_source",
    "manifest_from_literal",
    "manifest_from_ast_tree",
    "ManifestPath",
]


@dataclass(frozen=True, slots=True)
class ManifestPath:
    """Path to a ``__manifest__.py`` file, posix-style relative text.

    Existence is validated at the adapter layer, not here.
    """

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or self.value == "":
            raise ContractError("ManifestPath must be non-empty")
        if not self.value.endswith("__manifest__.py"):
            raise ContractError(f"ManifestPath must point to __manifest__.py, got {self.value!r}")

    @classmethod
    def of(cls, value: str) -> Self:
        """Build a manifest path value object."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


class ManifestParseError:
    """Discriminator constants for manifest parse failure reasons."""

    NO_DICT = "no_manifest_dict"
    NO_LITERAL = "literal_eval_failed"
    NO_ASSIGNMENT = "no_manifest_assignment"
    EMPTY = "empty_manifest"


@dataclass(frozen=True, slots=True)
class ManifestParseFailed:
    """Typed parse failure for one manifest source."""

    origin: ManifestPath | None
    reason: str
    message: str

    @property
    def path_text(self) -> str:
        """Return the origin path text or empty string."""
        return self.origin.value if self.origin is not None else ""


@dataclass(frozen=True, slots=True)
class Manifest:
    """Parsed Odoo manifest.

    Only the ``depends`` field is modeled today; ``raw`` is kept optional for
    debug/introspection at the boundary and is never used by domain rules.
    """

    depends: frozenset[ModuleName] = field(default_factory=frozenset)
    raw: dict[str, object] | None = None

    @classmethod
    def empty(cls) -> Self:
        """Build an empty manifest (no depends)."""
        return cls(depends=frozenset())

    @classmethod
    def empty_with_failure(cls, _failure: ManifestParseFailed) -> Self:
        """Build an empty manifest paired with a recorded parse failure.

        Domain code records the failure separately; the manifest is empty so
        downstream analysis can continue when policy allows it.
        """
        return cls.empty()

    @property
    def depends_names(self) -> tuple[str, ...]:
        """Return sorted depend names as plain strings (boundary convenience)."""
        return tuple(sorted(m.value for m in self.depends))


# --- AST-driven parsing ----------------------------------------------------


_MANIFEST_TARGET_NAMES = {"manifest", "__manifest__"}


def manifest_from_ast_tree(
    tree: ast.Module,
    origin: ManifestPath | None = None,
) -> Result[Manifest, ManifestParseFailed]:
    """Find the manifest literal in an AST module and parse it.

    Uses structural pattern matching over top-level statement forms:
    ``ast.Expr`` (bare dict literal) and ``ast.Assign`` (``manifest = {...}``).

    Mirrors the legacy parser's tolerance: statements that look like a manifest
    but whose value is not a dict (or fails ``literal_eval``) are skipped, and
    the search continues. Only the first successful dict wins; if none is found
    by end of module, ``NO_ASSIGNMENT`` is returned.
    """
    for node in tree.body:
        match node:
            case ast.Expr(value=value):
                result = _eval_manifest_value(value, origin)
                if result.is_ok():
                    return result
            case ast.Assign(targets=targets, value=value):
                if _has_manifest_target(targets):
                    result = _eval_manifest_value(value, origin)
                    if result.is_ok():
                        return result
            case _:
                continue
    return Error(
        ManifestParseFailed(
            origin=origin,
            reason=ManifestParseError.NO_ASSIGNMENT,
            message="No manifest dict found at module top level.",
        ),
    )


def _has_manifest_target(targets: list[ast.expr]) -> bool:
    """Return True if any assignment target is named ``manifest``/``__manifest__``."""
    for target in targets:
        match target:
            case ast.Name(id=name) if name in _MANIFEST_TARGET_NAMES:
                return True
            case _:
                continue
    return False


def _eval_manifest_value(
    value: ast.expr,
    origin: ManifestPath | None,
) -> Result[Manifest, ManifestParseFailed]:
    """literal_eval the manifest value node and build a :class:`Manifest`."""
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError) as exc:
        return Error(
            ManifestParseFailed(
                origin=origin,
                reason=ManifestParseError.NO_LITERAL,
                message=f"literal_eval failed: {exc}",
            ),
        )
    return manifest_from_literal(parsed, origin=origin)


def manifest_from_literal(
    value: object,
    origin: ManifestPath | None = None,
) -> Result[Manifest, ManifestParseFailed]:
    """Build a :class:`Manifest` from an already-evaluated literal value."""
    if not isinstance(value, dict):
        return Error(
            ManifestParseFailed(
                origin=origin,
                reason=ManifestParseError.NO_DICT,
                message="Manifest literal is not a dict.",
            ),
        )
    depends: set[ModuleName] = set()
    non_string_depends: list[object] = []
    raw_depends = value.get("depends", [])
    if isinstance(raw_depends, (list, tuple, set, frozenset)):
        for dep in raw_depends:
            match dep:
                case str() as name:
                    parsed = ModuleName.parse(name)
                    if parsed is not None:
                        depends.add(parsed)
                    else:
                        non_string_depends.append(dep)
                case _:
                    non_string_depends.append(dep)
    raw = {k: v for k, v in value.items()} if value else {}
    if non_string_depends:
        # Non-string depends are recorded but do not fail the whole manifest;
        # the bad entries are dropped from the typed frozenset.
        raw["_non_string_depends"] = non_string_depends
    return Ok(Manifest(depends=frozenset(depends), raw=raw or None))


def parse_manifest_source(
    source: str,
    origin: ManifestPath | None = None,
) -> Result[Manifest, ManifestParseFailed]:
    """Parse manifest source text into a :class:`Manifest` or typed failure."""
    try:
        tree = ast.parse(source, filename=origin.value if origin else "<manifest>")
    except SyntaxError as exc:
        return Error(
            ManifestParseFailed(
                origin=origin,
                reason=ManifestParseError.NO_LITERAL,
                message=f"manifest source syntax error: {exc}",
            ),
        )
    return manifest_from_ast_tree(tree, origin=origin)
