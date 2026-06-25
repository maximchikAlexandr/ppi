"""Pure AST extraction helpers using structural pattern matching.

These replace the ``isinstance`` chains in the legacy pipeline with declarative
``match node:`` forms. Unknown node shapes return ``None``/empty tuple (normal
"not a match" outcome), never raise — AST traversal must stay total.
"""

from __future__ import annotations

import ast

__all__ = [
    "extract_string_literal",
    "extract_string_list",
    "extract_target_names",
]


def extract_string_literal(node: ast.AST | None) -> str | None:
    """Extract a single string value from an AST literal when possible."""
    match node:
        case ast.Constant(value=str(value)):
            return value
        case _:
            return None


def extract_string_list(node: ast.AST | None) -> tuple[str, ...]:
    """Extract one or many string literals from an AST node.

    Returns a tuple (immutable) so callers can treat the result as a value.
    """
    match node:
        case None:
            return ()
        case ast.Constant(value=str(value)):
            return (value,)
        case ast.List(elts=elts) | ast.Tuple(elts=elts) | ast.Set(elts=elts):
            return tuple(
                item for child in elts if (item := extract_string_literal(child)) is not None
            )
        case _:
            return ()


def extract_target_names(node: ast.AST | None) -> tuple[str, ...]:
    """Extract assigned variable names from an assignment target node.

    Handles ``Name``, ``Tuple``/``List`` unpacking and ``Starred`` targets.
    """
    match node:
        case None:
            return ()
        case ast.Name(id=name):
            return (name,)
        case ast.Tuple(elts=elts) | ast.List(elts=elts):
            names: list[str] = []
            for child in elts:
                names.extend(extract_target_names(child))
            return tuple(names)
        case ast.Starred(value=value):
            return extract_target_names(value)
        case _:
            return ()
