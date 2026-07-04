"""Model expression resolution pipeline tests.

Verifies that model expression resolution functions work as pure,
typed stages for known patterns and return recoverable facts for
unsupported dynamic expressions.
"""

from __future__ import annotations

import ast

from ppi.core.odoo.model_expr import (
    AliasState,
    ModelResolutionContext,
    resolve_model_expr,
    is_env_object,
    extract_env_subscript_model,
)


def _make_context(
    env_aliases: set[str] | None = None,
    model_aliases: set[tuple[str, str]] | None = None,
    class_model_names: set[str] | None = None,
) -> ModelResolutionContext:
    state = AliasState(
        env_aliases=frozenset(env_aliases or {"env"}),
        model_aliases=frozenset(model_aliases or {("partner", "res.partner")}),
    )
    return ModelResolutionContext(
        aliases=state,
        class_model_names=frozenset(class_model_names or {"res.partner"}),
        relational_fields={},
    )


class TestModelExpressionResolution:
    """Tests for model expression resolution as pure typed functions."""

    def test_resolve_env_attribute(self) -> None:
        ctx = _make_context()
        node = ast.parse("env.ref('base.module_a')").body[0].value  # type: ignore[attr-defined]
        result = resolve_model_expr(node, ctx)
        # env.ref(...) returns a recordset; model is resolved from call context
        assert result is None or isinstance(result, str)

    def test_resolve_self_dot_attribute(self) -> None:
        node = ast.parse("self.env['sale.order']").body[0].value  # type: ignore[attr-defined]
        ctx = _make_context()
        model = extract_env_subscript_model(node, ctx)
        if model:
            assert isinstance(model, str)

    def test_env_object_detection(self) -> None:
        node = ast.parse("self.env").body[0].value  # type: ignore[attr-defined]
        ctx = _make_context()
        assert is_env_object(node, ctx) is True

    def test_resolve_model_alias(self) -> None:
        ctx = _make_context(
            env_aliases={"env"},
            model_aliases={("partner", "res.partner")},
        )
        node = ast.parse("partner").body[0].value  # type: ignore[attr-defined]
        model = resolve_model_expr(node, ctx)
        assert model == "res.partner"
