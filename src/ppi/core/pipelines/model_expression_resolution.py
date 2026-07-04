"""Model expression resolution pipeline stage.

Extracts alias state construction, env object detection, env-subscript
model extraction, and target-name resolution into pure typed functions.
"""

from __future__ import annotations

from collections.abc import Iterable

from ppi.core.odoo.model_expr import (
    AliasState,
    ModelResolutionContext,
    extract_env_subscript_model,
    is_env_object,
    resolve_model_expr,
)


def build_alias_state(
    env_aliases: Iterable[str],
    model_aliases: Iterable[tuple[str, str]],
) -> AliasState:
    """Build an immutable alias state from env/model alias collections."""
    return AliasState(
        env_aliases=frozenset(env_aliases),
        model_aliases=frozenset(model_aliases),
    )


def build_resolution_context(
    aliases: AliasState,
    class_model_names: frozenset[str],
    relational_fields: dict[str, dict[str, str]] | None = None,
) -> ModelResolutionContext:
    """Build an immutable resolution context."""
    return ModelResolutionContext(
        aliases=aliases,
        class_model_names=class_model_names,
        relational_fields=relational_fields or {},
    )


def model_expression_resolution_pipeline(
    env_aliases: Iterable[str],
    model_aliases: Iterable[tuple[str, str]],
    class_model_names: frozenset[str],
    relational_fields: dict[str, dict[str, str]] | None = None,
) -> tuple[AliasState, ModelResolutionContext]:
    """Spec-named pipeline: build alias state and resolution context."""
    alias_state = build_alias_state(env_aliases, model_aliases)
    context = build_resolution_context(alias_state, class_model_names, relational_fields)
    return (alias_state, context)


__all__ = [
    "build_alias_state",
    "build_resolution_context",
    "resolve_model_expr",
    "is_env_object",
    "extract_env_subscript_model",
    "model_expression_resolution_pipeline",
]
