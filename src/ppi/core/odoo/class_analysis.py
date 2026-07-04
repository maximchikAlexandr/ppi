"""Odoo Python class analysis: AST visitors and per-file analysis."""
from __future__ import annotations

import ast
import sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

from ppi.core.odoo.ast_extract import extract_string_list, extract_string_literal, extract_target_names
from ppi.core.odoo.ast_facts import edge_kind_for_relational_field
from ppi.core.odoo.model_expr import (
    AliasState,
    ModelResolutionContext,
    extract_env_subscript_model,
    is_env_object,
    resolve_model_expr,
)
from ppi.core.odoo.types import ClassSummary, ModuleInfo

RELATIONAL_FIELD_TYPES = {"Many2one", "One2many", "Many2many"}
IGNORED_MODEL_ATTRIBUTE_NAMES = {
    "id", "ids", "display_name", "env", "_name", "_context", "_origin",
}


class MethodAnalyzer(ast.NodeVisitor):
    def __init__(
        self,
        model_names: frozenset[str],
        global_relational_fields: dict[str, dict[str, str]],
    ) -> None:
        self.model_names = model_names
        self.global_relational_fields = global_relational_fields
        self.env_aliases: set[str] = set()
        self.model_aliases: dict[str, str] = {}
        self.env_accesses: list[tuple[str, int]] = []
        self.method_calls: list[tuple[str, str, int]] = []
        self.field_property_accesses: list[tuple[str, str, int]] = []
        self.node_stack: list[ast.AST] = []

    def _build_context(self) -> ModelResolutionContext:
        state = AliasState(
            env_aliases=frozenset(self.env_aliases),
            model_aliases=frozenset(self.model_aliases.items()),
        )
        return ModelResolutionContext(
            aliases=state,
            class_model_names=self.model_names,
            relational_fields=self.global_relational_fields,
        )

    def visit(self, node: ast.AST) -> Any:
        self.node_stack.append(node)
        try:
            return super().visit(node)
        finally:
            self.node_stack.pop()

    def _get_parent_node(self) -> ast.AST | None:
        if len(self.node_stack) < 2:
            return None
        return self.node_stack[-2]

    def _register_aliases(self, target: ast.AST | None, model_name: str | None) -> None:
        if not model_name:
            return
        for target_name in extract_target_names(target):
            self.model_aliases[target_name] = model_name

    def visit_Assign(self, node: ast.Assign) -> None:
        ctx = self._build_context()
        target_names: list[str] = []
        for target in node.targets:
            target_names.extend(extract_target_names(target))
        if target_names and is_env_object(node.value, ctx):
            self.env_aliases.update(target_names)

        model_name = resolve_model_expr(node.value, ctx)
        if target_names and model_name:
            for target in node.targets:
                self._register_aliases(target, model_name)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if not isinstance(node.target, ast.Name) or node.value is None:
            self.generic_visit(node)
            return

        ctx = self._build_context()
        if is_env_object(node.value, ctx):
            self.env_aliases.add(node.target.id)

        self._register_aliases(node.target, resolve_model_expr(node.value, ctx))

        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        ctx = self._build_context()
        self._register_aliases(node.target, resolve_model_expr(node.iter, ctx))
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        ctx = self._build_context()
        self._register_aliases(node.target, resolve_model_expr(node.iter, ctx))
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        ctx = self._build_context()
        for item in node.items:
            self._register_aliases(
                item.optional_vars,
                resolve_model_expr(item.context_expr, ctx),
            )
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        ctx = self._build_context()
        for item in node.items:
            self._register_aliases(
                item.optional_vars,
                resolve_model_expr(item.context_expr, ctx),
            )
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        ctx = self._build_context()
        self._register_aliases(node.target, resolve_model_expr(node.value, ctx))
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        ctx = self._build_context()
        model_name = extract_env_subscript_model(node, ctx)
        if model_name:
            self.env_accesses.append((model_name, getattr(node, "lineno", 0)))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            ctx = self._build_context()
            model_name = resolve_model_expr(node.func.value, ctx)
            if model_name:
                self.method_calls.append(
                    (model_name, node.func.attr, getattr(node, "lineno", 0)),
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        parent = self._get_parent_node()
        if isinstance(parent, ast.Call) and parent.func is node:
            self.generic_visit(node)
            return
        if node.attr in IGNORED_MODEL_ATTRIBUTE_NAMES or node.attr.startswith("__"):
            self.generic_visit(node)
            return

        ctx = self._build_context()
        model_name = resolve_model_expr(node.value, ctx)
        if model_name:
            self.field_property_accesses.append(
                (model_name, node.attr, getattr(node, "lineno", 0)),
            )
        self.generic_visit(node)


def get_class_target_models(class_summary: ClassSummary) -> set[str]:
    return set(class_summary.declared_models or class_summary.inherit_models)


def build_class_summary(
    class_node: ast.ClassDef,
    file_path: Path,
    global_relational_fields: dict[str, dict[str, str]],
) -> ClassSummary:
    data = _extract_assignments(class_node.body)
    _merge_inherited_fields(data, global_relational_fields)
    _analyze_methods(class_node.body, data, global_relational_fields)
    return ClassSummary(
        file_path=file_path,
        class_name=class_node.name,
        model_names=frozenset(data["model_names"]),
        declared_models=frozenset(data["declared_models"]),
        inherit_models=frozenset(data["inherit_models"]),
        inherit_links=tuple(data["inherit_links"]),
        declared_methods=frozenset(data["declared_methods"]),
        declared_field_models=dict(data["declared_field_models"]),
        field_models=dict(data["field_models"]),
        field_links=tuple(data["field_links"]),
        related_paths=tuple(data["related_paths"]),
        depends_paths=tuple(data["depends_paths"]),
        onchange_paths=tuple(data["onchange_paths"]),
        constrains_paths=tuple(data["constrains_paths"]),
        env_accesses=tuple(data["env_accesses"]),
        method_calls=tuple(data["method_calls"]),
        field_property_accesses=tuple(data["field_property_accesses"]),
    )


def _extract_assignments(body: list[ast.stmt]) -> dict:
    declared_models: set[str] = set()
    inherit_models: set[str] = set()
    inherit_links: list[tuple[str, int]] = []
    field_models: dict[str, str] = {}
    declared_field_models: dict[str, str] = {}
    field_links: list[tuple[str, str, int, str]] = []
    related_paths: list[tuple[str, int, str]] = []

    for statement in body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        assigned_targets: list[str] = []
        assigned_value: ast.AST | None = None

        if isinstance(statement, ast.Assign):
            assigned_targets = [
                target.id for target in statement.targets if isinstance(target, ast.Name)
            ]
            assigned_value = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            assigned_targets = [statement.target.id]
            assigned_value = statement.value

        if assigned_targets:
            if "_name" in assigned_targets:
                declared_models.update(extract_string_list(assigned_value))
            if "_inherit" in assigned_targets:
                inherit_values = extract_string_list(assigned_value)
                inherit_models.update(inherit_values)
                inherit_line = getattr(statement, "lineno", 0)
                for inherit_model in inherit_values:
                    inherit_links.append((inherit_model, inherit_line))

        if not assigned_targets or assigned_value is None:
            continue

        field_name = assigned_targets[0]
        if not isinstance(assigned_value, ast.Call):
            continue
        if not isinstance(assigned_value.func, ast.Attribute):
            continue
        if not isinstance(assigned_value.func.value, ast.Name):
            continue
        if assigned_value.func.value.id != "fields":
            continue

        field_type = assigned_value.func.attr
        comodel_name = None
        related_path = None

        if field_type in RELATIONAL_FIELD_TYPES:
            if assigned_value.args:
                comodel_name = extract_string_literal(assigned_value.args[0])
            if comodel_name is None:
                for keyword in assigned_value.keywords:
                    if keyword.arg == "comodel_name":
                        comodel_name = extract_string_literal(keyword.value)
                        break
            if comodel_name:
                field_models[field_name] = comodel_name
                declared_field_models[field_name] = comodel_name
                kind_enum = edge_kind_for_relational_field(field_type)
                kind = kind_enum.value if kind_enum is not None else f"python_{field_type.lower()}"
                line = getattr(statement, "lineno", 0)
                detail = f"{field_name} -> {comodel_name}"
                field_links.append((kind, comodel_name, line, detail))

        for keyword in assigned_value.keywords:
            if keyword.arg == "related":
                related_path = extract_string_literal(keyword.value)
                break
        if related_path:
            line = getattr(statement, "lineno", 0)
            related_paths.append((related_path, line, field_name))

    model_names = set(declared_models) or set(inherit_models)

    return dict(
        declared_models=declared_models,
        inherit_models=inherit_models,
        inherit_links=inherit_links,
        model_names=model_names,
        field_models=field_models,
        declared_field_models=declared_field_models,
        field_links=field_links,
        related_paths=related_paths,
    )


def _merge_inherited_fields(
    data: dict,
    global_relational_fields: dict[str, dict[str, str]],
) -> None:
    inherited: dict[str, str] = {}
    for model_name in data["model_names"]:
        inherited.update(global_relational_fields.get(model_name, {}))
    if inherited:
        inherited.update(data["field_models"])
        data["field_models"] = inherited


def _analyze_methods(
    body: list[ast.stmt],
    data: dict,
    global_relational_fields: dict[str, dict[str, str]],
) -> None:
    declared_methods: set[str] = set()
    depends_paths: list[tuple[str, int, str]] = []
    onchange_paths: list[tuple[str, int, str]] = []
    constrains_paths: list[tuple[str, int, str]] = []
    env_accesses: list[tuple[str, int]] = []
    method_calls: list[tuple[str, str, int]] = []
    field_property_accesses: list[tuple[str, str, int]] = []

    for statement in body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        declared_methods.add(statement.name)

        for decorator in statement.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue
            if not (
                isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "api"
            ):
                continue

            decorator_targets = {
                "depends": depends_paths,
                "onchange": onchange_paths,
                "constrains": constrains_paths,
            }
            target_list = decorator_targets.get(decorator.func.attr)
            if target_list is None:
                continue

            line = getattr(decorator, "lineno", 0)
            for argument in decorator.args:
                for field_path in extract_string_list(argument):
                    target_list.append((field_path, line, statement.name))

        analyzer = MethodAnalyzer(
            model_names=frozenset(data["model_names"]),
            global_relational_fields=global_relational_fields,
        )
        analyzer.visit(statement)
        env_accesses.extend(analyzer.env_accesses)
        method_calls.extend(analyzer.method_calls)
        field_property_accesses.extend(analyzer.field_property_accesses)

    data["declared_methods"] = declared_methods
    data["depends_paths"] = depends_paths
    data["onchange_paths"] = onchange_paths
    data["constrains_paths"] = constrains_paths
    data["env_accesses"] = env_accesses
    data["method_calls"] = method_calls
    data["field_property_accesses"] = field_property_accesses


def analyze_python_file(
    file_path: Path,
    global_relational_fields: dict[str, dict[str, str]],
) -> list[ClassSummary]:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))

    return [
        build_class_summary(stmt, file_path, global_relational_fields)
        for stmt in tree.body
        if isinstance(stmt, ast.ClassDef)
    ]


def analyze_python_modules(modules: dict[str, ModuleInfo]) -> dict[str, ModuleInfo]:
    global_relational_fields: dict[str, dict[str, str]] = defaultdict(dict)
    result: dict[str, ModuleInfo] = {}

    for module_name in sorted(modules):
        module = modules[module_name]
        new_class_summaries: list[ClassSummary] = list(module.class_summaries)

        for file_path in sorted(module.path.rglob("*.py")):
            if file_path.name == "__manifest__.py":
                continue
            try:
                class_summaries = analyze_python_file(
                    file_path=file_path,
                    global_relational_fields=global_relational_fields,
                )
            except SyntaxError as exc:
                print(f"[WARN] Invalid Python {file_path}: {exc}", file=sys.stderr)
                continue
            except UnicodeDecodeError as exc:
                print(f"[WARN] Cannot decode Python {file_path}: {exc}", file=sys.stderr)
                continue
            new_class_summaries.extend(class_summaries)

            for class_summary in class_summaries:
                for target_model in get_class_target_models(class_summary):
                    for field_name, comodel_name in class_summary.field_models.items():
                        global_relational_fields[target_model][field_name] = comodel_name

        declared_models: set[str] = set(module.declared_models)
        inherited_models: set[str] = set(module.inherited_models)
        for class_summary in new_class_summaries:
            declared_models.update(
                model_name
                for model_name in class_summary.declared_models
                if model_name not in class_summary.inherit_models
            )
            inherited_models.update(class_summary.inherit_models)

        result[module_name] = replace(module,
            class_summaries=tuple(new_class_summaries),
            declared_models=frozenset(declared_models),
            inherited_models=frozenset(inherited_models),
        )

    return result
