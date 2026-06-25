"""Pure Odoo model-expression resolvers using structural pattern matching.

These extract the logic from :class:`ppi.core.odoo.pipeline.MethodAnalyzer`
private methods (``_resolve_model_expr``, ``_is_env_object``,
``_extract_env_subscript_model``) so it can be unit-tested on tiny AST
fragments without running the full visitor.

The visitor stays as a traversal shell (``ast.NodeVisitor``) and only calls
these pure resolvers, populating a local builder with typed facts.

Context (env aliases, model aliases, current class model names, relational
field map) is passed through an immutable :class:`ModelResolutionContext`.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Self

from ppi.core.odoo.ast_extract import extract_string_literal

__all__ = [
    "ModelResolutionContext",
    "resolve_model_expr",
    "extract_env_subscript_model",
    "is_env_object",
    "AliasState",
    "extract_alias_targets",
]

_IGNORED_MODEL_ATTRIBUTE_NAMES = {
    "id",
    "ids",
    "display_name",
    "env",
    "_name",
    "_context",
    "_origin",
}
_RECORDSET_CHAIN_METHODS = {
    "sudo",
    "with_context",
    "with_company",
    "with_user",
    "with_env",
    "search",
    "browse",
    "filtered",
    "filtered_domain",
    "sorted",
    "exists",
    "mapped",
}


@dataclass(frozen=True, slots=True)
class AliasState:
    """Immutable snapshot of alias bindings at one point in traversal.

    ``env_aliases`` are names bound to ``self.env``; ``model_aliases`` maps a
    name to a resolved model name. Both are immutable so the resolver can be
    tested without mutation.
    """

    env_aliases: frozenset[str] = field(default_factory=frozenset)
    model_aliases: frozenset[tuple[str, str]] = field(default_factory=frozenset)

    @classmethod
    def empty(cls) -> Self:
        """Build an empty alias state."""
        return cls()

    def with_env_alias(self, name: str) -> AliasState:
        """Return a new state with one env alias added."""
        return AliasState(env_aliases=self.env_aliases | {name}, model_aliases=self.model_aliases)

    def with_model_alias(self, name: str, model: str) -> AliasState:
        """Return a new state with one model alias binding added."""
        return AliasState(
            env_aliases=self.env_aliases,
            model_aliases=self.model_aliases | {(name, model)},
        )

    def model_for(self, name: str) -> str | None:
        """Return the model bound to ``name`` if any."""
        for alias_name, model in self.model_aliases:
            if alias_name == name:
                return model
        return None

    def is_env_alias(self, name: str) -> bool:
        """Return True if ``name`` is bound to ``self.env``."""
        return name in self.env_aliases


@dataclass(frozen=True, slots=True)
class ModelResolutionContext:
    """Immutable context passed to the pure model resolvers.

    ``class_model_names`` is the set of model names declared/inherited by the
    class currently being analyzed (used to resolve ``self`` when the class
    owns exactly one model). ``relational_fields`` maps
    ``{model: {field: comodel}}`` for relational field comodel resolution.
    """

    aliases: AliasState = field(default_factory=AliasState)
    class_model_names: frozenset[str] = field(default_factory=frozenset)
    relational_fields: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> Self:
        """Build an empty resolution context."""
        return cls()

    def with_aliases(self, aliases: AliasState) -> ModelResolutionContext:
        """Return a new context with replaced alias state."""
        return ModelResolutionContext(
            aliases=aliases,
            class_model_names=self.class_model_names,
            relational_fields=self.relational_fields,
        )


def is_env_object(node: ast.AST, context: ModelResolutionContext) -> bool:
    """Check if AST node points to ``self.env`` or one of its aliases."""
    match node:
        case ast.Attribute(value=ast.Name(id="self"), attr="env"):
            return True
        case ast.Name(id=name) if context.aliases.is_env_alias(name):
            return True
        case _:
            return False


def extract_env_subscript_model(
    node: ast.AST,
    context: ModelResolutionContext,
) -> str | None:
    """Extract the model name from ``self.env['model.name']`` access."""
    match node:
        case ast.Subscript(value=value, slice=slice_node) if is_env_object(value, context):
            return extract_string_literal(slice_node)
        case _:
            return None


def resolve_model_expr(node: ast.AST, context: ModelResolutionContext) -> str | None:
    """Resolve a model name from a recordset expression.

    Uses structural pattern matching over the AST forms that carry model
    information: ``Subscript`` (``env['m']``), ``Name`` (alias/self),
    ``Attribute`` (relational field traversal), ``Call`` (recordset chain
    methods and ``super()``).
    """
    if model := extract_env_subscript_model(node, context):
        return model

    match node:
        case ast.Name(id=name):
            if model := context.aliases.model_for(name):
                return model
            if name == "self" and len(context.class_model_names) == 1:
                return next(iter(context.class_model_names))
            return None

        case ast.Attribute(value=value, attr=attr):
            base_model = resolve_model_expr(value, context)
            if base_model is None:
                return None
            comodel = context.relational_fields.get(base_model, {}).get(attr)
            return comodel if comodel is not None else base_model

        case ast.Call(func=ast.Attribute(value=value, attr=attr)) if (
            attr in _RECORDSET_CHAIN_METHODS
        ):
            return resolve_model_expr(value, context)

        case ast.Call(func=ast.Name(id="super")) if len(context.class_model_names) == 1:
            return next(iter(context.class_model_names))

        case _:
            return None


def extract_alias_targets(
    target: ast.AST | None,
    model_name: str | None,
    state: AliasState,
) -> AliasState:
    """Return a new alias state with targets bound to ``model_name``.

    If ``model_name`` is falsy, the state is returned unchanged. Used by the
    visitor shell to register aliases from assignments/for/with/etc.
    """
    from ppi.core.odoo.ast_extract import extract_target_names  # local to avoid cycle

    if not model_name:
        return state
    new_state = state
    for name in extract_target_names(target):
        new_state = new_state.with_model_alias(name, model_name)
    return new_state
