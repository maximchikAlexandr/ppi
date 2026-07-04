"""Odoo code metrics: file line counts, Python complexity, AST node density."""
from __future__ import annotations

import ast
import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any

import complexipy
from radon.visitors import ComplexityVisitor

from ppi.core.odoo.complexity import (
    ComplexityMetrics,
    FileComplexityAnalysisResult,
    FileComplexityInfo,
)
from ppi.core.odoo.dist_stats import build_distribution_stats
from ppi.core.odoo.file_classification import classify_relative_file
from ppi.core.odoo.types import FileLineInfo
from ppi.core.odoo.types import ModuleInfo
from ppi.core.value_objects import LineCategory


def count_file_lines(file_path: Path) -> int:
    with file_path.open("r", encoding="utf-8", errors="ignore") as file_obj:
        return sum(1 for _ in file_obj)


def classify_file(file_path: Path, module_path: Path) -> str | None:
    relative_path = file_path.relative_to(module_path).as_posix()
    category = classify_relative_file(relative_path)
    return category.value if category is not None else None


def is_test_file(file_path: Path, module_path: Path) -> bool:
    relative_parts = file_path.relative_to(module_path).parts
    file_name = file_path.name.lower()
    if "tests" in relative_parts or "__tests__" in relative_parts:
        return True
    if file_name.startswith("test_") or file_name.endswith("_test.py"):
        return True
    if file_name.endswith(".test.js") or file_name.endswith(".spec.js"):
        return True
    return False


def file_top_folder(relative_path: str) -> str:
    parts = relative_path.split("/")
    return parts[0] if len(parts) > 1 else "."


def module_python_file_count(module: ModuleInfo) -> int:
    return len(module.python_complexity_files)


# --- Module code size -------------------------------------------------------


def analyze_module_code_size_for_module(module: ModuleInfo) -> ModuleInfo:
    counters = dict.fromkeys((category.value for category in LineCategory), 0)
    files: list[FileLineInfo] = []
    for file_path in sorted(module.path.rglob("*")):
        if not file_path.is_file():
            continue
        category = classify_file(file_path, module.path)
        if category is None:
            continue
        line_count = count_file_lines(file_path)
        counters[category] += line_count
        relative_path = file_path.relative_to(module.path).as_posix()
        files.append(
            FileLineInfo(
                relative_path=relative_path,
                lines=line_count,
                category=category,
            ),
        )
    return replace(
        module,
        files=tuple(files),
        total_lines=sum(counters.values()),
        **counters,
    )


def analyze_module_code_size(modules: dict[str, ModuleInfo]) -> dict[str, ModuleInfo]:
    return {
        k: analyze_module_code_size_for_module(v) for k, v in modules.items()
    }


# --- Python complexity ------------------------------------------------------


class JonesComplexityVisitor(ast.NodeVisitor):
    """Count AST nodes per physical source line."""

    def __init__(self) -> None:
        self.line_nodes: dict[int, int] = defaultdict(int)

    def generic_visit(self, node: ast.AST) -> None:
        if not isinstance(node, (ast.Module, ast.Load, ast.Store, ast.Del, ast.expr_context)):
            line_no = getattr(node, "lineno", None)
            if isinstance(line_no, int) and line_no > 0:
                self.line_nodes[line_no] += 1
        super().generic_visit(node)


def iter_radon_function_blocks(blocks: Iterable[Any]) -> Iterable[Any]:
    for block in blocks:
        if hasattr(block, "methods"):
            yield from iter_radon_function_blocks(getattr(block, "methods", []))
        if type(block).__name__ == "Function":
            yield block
            yield from iter_radon_function_blocks(getattr(block, "closures", []))


def collect_cyclomatic_scores(source: str) -> list[int]:
    visitor = ComplexityVisitor.from_code(source)
    return [int(block.complexity) for block in iter_radon_function_blocks(visitor.blocks)]


def collect_cognitive_scores(source: str) -> list[int]:
    code_metrics = complexipy.code_complexity(source)
    return [int(item.complexity) for item in code_metrics.functions]


def collect_jones_line_scores(tree: ast.AST) -> list[int]:
    visitor = JonesComplexityVisitor()
    visitor.visit(tree)
    return [visitor.line_nodes[line_no] for line_no in sorted(visitor.line_nodes)]


def attach_file_complexity_to_line_info(
    file_infos: list[FileLineInfo],
    relative_path: str,
    metrics: ComplexityMetrics | None,
    parse_error: str | None,
) -> list[FileLineInfo]:
    return [
        replace(file_info, complexity=metrics, parse_error=parse_error)
        if file_info.relative_path == relative_path
        else file_info
        for file_info in file_infos
    ]


def build_file_complexity_error_result(
    file_path: Path,
    relative_path: str,
    line_count: int,
    error: Exception,
    warning_label: str,
) -> FileComplexityAnalysisResult:
    print(
        f"[WARN] {warning_label} {file_path}: {error}",
        file=sys.stderr,
    )
    return FileComplexityAnalysisResult(
        file_complexity_info=FileComplexityInfo(
            relative_path=relative_path,
            lines=line_count,
            function_count=0,
            jones_line_count=0,
            complexity=ComplexityMetrics(),
            parse_error=str(error),
        ),
    )


def analyze_python_complexity_file(
    file_path: Path,
    module_path: Path,
) -> FileComplexityAnalysisResult:
    relative_path = file_path.relative_to(module_path).as_posix()
    line_count = count_file_lines(file_path)

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        return build_file_complexity_error_result(
            file_path, relative_path, line_count, exc,
            "Invalid Python for complexity",
        )
    except UnicodeDecodeError as exc:
        return build_file_complexity_error_result(
            file_path, relative_path, line_count, exc,
            "Cannot decode Python for complexity",
        )

    try:
        function_scores_cc = tuple(collect_cyclomatic_scores(source))
        function_scores_cognitive = tuple(collect_cognitive_scores(source))
    except Exception as exc:
        return build_file_complexity_error_result(
            file_path, relative_path, line_count, exc,
            "Complexity library failure",
        )

    jones_values = tuple(collect_jones_line_scores(tree))
    file_metrics = ComplexityMetrics(
        cyclomatic=build_distribution_stats(function_scores_cc),
        cognitive=build_distribution_stats(function_scores_cognitive),
        jones=build_distribution_stats(jones_values),
    )
    return FileComplexityAnalysisResult(
        file_complexity_info=FileComplexityInfo(
            relative_path=relative_path,
            lines=line_count,
            function_count=len(function_scores_cc),
            jones_line_count=len(jones_values),
            complexity=file_metrics,
            parse_error=None,
        ),
        cyclomatic_values=function_scores_cc,
        cognitive_values=function_scores_cognitive,
        jones_values=jones_values,
    )


def analyze_python_complexity_for_module(module: ModuleInfo) -> ModuleInfo:
    python_files = [
        file_path
        for file_path in sorted(module.path.rglob("*.py"))
        if file_path.name != "__manifest__.py" and not is_test_file(file_path, module.path)
    ]
    results = [analyze_python_complexity_file(file_path, module.path) for file_path in python_files]

    updated_files = module.files
    for result in results:
        updated_files = attach_file_complexity_to_line_info(
            updated_files,
            result.file_complexity_info.relative_path,
            result.file_complexity_info.complexity,
            result.file_complexity_info.parse_error,
        )

    cyclomatic_values = [value for result in results for value in result.cyclomatic_values]
    cognitive_values = [value for result in results for value in result.cognitive_values]
    jones_values = [value for result in results for value in result.jones_values]

    return replace(
        module,
        files=tuple(updated_files),
        python_complexity_files=tuple(result.file_complexity_info for result in results),
        python_complexity_parse_errors=sum(
            1 for result in results if result.file_complexity_info.parse_error
        ),
        complexity=ComplexityMetrics(
            cyclomatic=build_distribution_stats(cyclomatic_values),
            cognitive=build_distribution_stats(cognitive_values),
            jones=build_distribution_stats(jones_values),
        ),
    )


def analyze_python_complexity(modules: dict[str, ModuleInfo]) -> dict[str, ModuleInfo]:
    return {
        k: analyze_python_complexity_for_module(v) for k, v in modules.items()
    }


# --- Enrichment composition -------------------------------------------------


def enrich_modules_with_code_analysis(artifacts: AnalysisArtifacts) -> AnalysisArtifacts:
    with_code_size = analyze_module_code_size(artifacts.modules)
    with_complexity = analyze_python_complexity(with_code_size)
    return replace(artifacts, modules=with_complexity)
