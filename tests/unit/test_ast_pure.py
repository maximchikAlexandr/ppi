"""Unit tests for pure AST extract and model-expression resolvers."""

from __future__ import annotations

import ast

import pytest

from ppi.core.odoo.ast_extract import (
    extract_string_list,
    extract_string_literal,
    extract_target_names,
)
from ppi.core.odoo.ast_facts import (
    DecoratorPath,
    EnvAccess,
    FieldLink,
    InheritLink,
    MethodCallFact,
    edge_kind_for_relational_field,
)
from ppi.core.odoo.model_expr import (
    AliasState,
    ModelResolutionContext,
    extract_alias_targets,
    extract_env_subscript_model,
    is_env_object,
    resolve_model_expr,
)
from ppi.core.value_objects import EdgeKind, ModelName, SourceLine


def _expr(src: str) -> ast.expr:
    return ast.parse(src).body[0].value  # type: ignore[union-attr]


def _target(src: str) -> ast.expr:
    return ast.parse(src).body[0].targets[0]  # type: ignore[union-attr]


# --- ast_extract -----------------------------------------------------------


def test_extract_string_literal_string():
    assert extract_string_literal(_expr('"x"')) == "x"


def test_extract_string_literal_non_string():
    assert extract_string_literal(_expr("1")) is None
    assert extract_string_literal(None) is None


def test_extract_string_list_list():
    assert extract_string_list(_expr("['a', 'b', 1]")) == ("a", "b")


def test_extract_string_list_tuple():
    assert extract_string_list(_expr("('a',)")) == ("a",)


def test_extract_string_list_set():
    assert extract_string_list(_expr("{'a'}")) == ("a",)


def test_extract_string_list_none():
    assert extract_string_list(None) == ()


def test_extract_string_list_unknown_node():
    assert extract_string_list(_expr("x")) == ()


def test_extract_target_names_name():
    assert extract_target_names(_target("x = 1")) == ("x",)


def test_extract_target_names_tuple():
    assert extract_target_names(_target("a, b = 1, 2")) == ("a", "b")


def test_extract_target_names_starred():
    assert extract_target_names(_target("a, *b = xs")) == ("a", "b")


def test_extract_target_names_none():
    assert extract_target_names(None) == ()


# --- ast_facts -------------------------------------------------------------


def test_inherit_link():
    link = InheritLink(model=ModelName.of("sale.order"), line=SourceLine.of(3))
    assert link.model.value == "sale.order"
    assert int(link.line) == 3  # type: ignore[arg-type]


def test_field_link():
    fl = FieldLink(
        kind=EdgeKind.PYTHON_MANY2ONE,
        comodel=ModelName.of("res.partner"),
        line=SourceLine.of(7),
        detail="d",
    )
    assert fl.kind is EdgeKind.PYTHON_MANY2ONE


def test_decorator_path_rejects_invalid_decorator():
    with pytest.raises(ValueError):
        DecoratorPath(field_path="x", line=None, method_name="m", decorator="bogus")


def test_decorator_path_valid():
    dp = DecoratorPath(
        field_path="x", line=SourceLine.of(1), method_name="m", decorator="depends"
    )
    assert dp.decorator == "depends"


def test_env_access():
    ea = EnvAccess(model=ModelName.of("res.partner"), line=SourceLine.of(2))
    assert ea.model.value == "res.partner"


def test_method_call_fact():
    mc = MethodCallFact(model=ModelName.of("res.partner"), method="search", line=None)
    assert mc.method == "search"


def test_edge_kind_for_relational_field():
    assert edge_kind_for_relational_field("Many2one") is EdgeKind.PYTHON_MANY2ONE
    assert edge_kind_for_relational_field("One2many") is EdgeKind.PYTHON_ONE2MANY
    assert edge_kind_for_relational_field("Many2many") is EdgeKind.PYTHON_MANY2MANY
    assert edge_kind_for_relational_field("Char") is None


# --- model_expr ------------------------------------------------------------


def test_extract_env_subscript_model():
    ctx = ModelResolutionContext.empty()
    assert extract_env_subscript_model(_expr("self.env['sale.order']"), ctx) == "sale.order"
    assert extract_env_subscript_model(_expr("self"), ctx) is None


def test_resolve_model_expr_env_subscript():
    ctx = ModelResolutionContext.empty()
    assert resolve_model_expr(_expr("self.env['sale.order']"), ctx) == "sale.order"


def test_resolve_model_expr_self_single_model():
    ctx = ModelResolutionContext(class_model_names=frozenset({"sale.order"}))
    assert resolve_model_expr(_expr("self"), ctx) == "sale.order"


def test_resolve_model_expr_self_multiple_models():
    ctx = ModelResolutionContext(class_model_names=frozenset({"a", "b"}))
    assert resolve_model_expr(_expr("self"), ctx) is None


def test_resolve_model_expr_alias():
    state = AliasState.empty().with_model_alias("rec", "sale.order")
    ctx = ModelResolutionContext(aliases=state, class_model_names=frozenset({"sale.order"}))
    assert resolve_model_expr(_expr("rec"), ctx) == "sale.order"


def test_resolve_model_expr_recordset_chain():
    state = AliasState.empty().with_model_alias("rec", "sale.order")
    ctx = ModelResolutionContext(aliases=state, class_model_names=frozenset({"sale.order"}))
    assert resolve_model_expr(_expr("rec.sudo()"), ctx) == "sale.order"
    assert resolve_model_expr(_expr("rec.search()"), ctx) == "sale.order"


def test_resolve_model_expr_attribute_relational():
    state = AliasState.empty().with_model_alias("rec", "sale.order")
    ctx = ModelResolutionContext(
        aliases=state,
        class_model_names=frozenset({"sale.order"}),
        relational_fields={"sale.order": {"partner_id": "res.partner"}},
    )
    assert resolve_model_expr(_expr("rec.partner_id"), ctx) == "res.partner"


def test_resolve_model_expr_attribute_no_comodel_returns_base():
    state = AliasState.empty().with_model_alias("rec", "sale.order")
    ctx = ModelResolutionContext(
        aliases=state,
        class_model_names=frozenset({"sale.order"}),
        relational_fields={"sale.order": {}},
    )
    assert resolve_model_expr(_expr("rec.other"), ctx) == "sale.order"


def test_resolve_model_expr_super_single_model():
    ctx = ModelResolutionContext(class_model_names=frozenset({"sale.order"}))
    assert resolve_model_expr(_expr("super()"), ctx) == "sale.order"


def test_resolve_model_expr_unknown_node_returns_none():
    ctx = ModelResolutionContext.empty()
    assert resolve_model_expr(_expr("42"), ctx) is None


def test_is_env_object_self_env():
    ctx = ModelResolutionContext.empty()
    assert is_env_object(_expr("self.env"), ctx) is True


def test_is_env_object_alias():
    state = AliasState.empty().with_env_alias("env_obj")
    ctx = ModelResolutionContext(aliases=state)
    assert is_env_object(_expr("env_obj"), ctx) is True


def test_is_env_object_other():
    ctx = ModelResolutionContext.empty()
    assert is_env_object(_expr("self.other"), ctx) is False


def test_extract_alias_targets_binds_models():
    state = AliasState.empty()
    new_state = extract_alias_targets(_target("a, b = 1"), "sale.order", state)
    assert new_state.model_for("a") == "sale.order"
    assert new_state.model_for("b") == "sale.order"


def test_extract_alias_targets_no_model_returns_unchanged():
    state = AliasState.empty()
    new_state = extract_alias_targets(_target("a = 1"), None, state)
    assert new_state is state


def test_alias_state_with_env_alias():
    s = AliasState.empty().with_env_alias("e")
    assert s.is_env_alias("e")
    assert not s.is_env_alias("x")