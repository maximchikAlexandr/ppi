"""Odoo-specific data types for analysis pipelines."""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from ppi.core.odoo.complexity import ComplexityMetrics, FileComplexityInfo
from ppi.core.odoo.facts import CouplingEdgeSnapshot
from ppi.core.value_objects import ContractError, LineCategory

__all__ = [
    "AnalysisArtifacts",
    "CouplingEdgeAccumulator",
    "ClassSummary",
    "ModuleInfo",
    "ModuleFacts",
    "ReportConfig",
    "FileLineInfo",
    "LineCategoryCount",
    "LineCategoryCounts",
    "freeze_module_info",
]


@dataclass(frozen=True, slots=True)
class ReportConfig:
    project_label: str
    module_prefixes: tuple[str, ...] = ()
    include_modules: tuple[str, ...] = ()
    all_modules: bool = False


@dataclass(frozen=True, slots=True)
class AnalysisArtifacts:
    addons_paths: tuple[Path, ...]
    config: ReportConfig
    modules: dict[str, ModuleInfo]
    model_owners: dict[str, set[str]] = field(default_factory=dict)
    field_providers: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    method_providers: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    edge_snapshots: tuple[CouplingEdgeSnapshot, ...] = ()
    module_scores: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass(slots=True)
class CouplingEdgeAccumulator:
    source_module: str
    target_module: str
    kind_counter: Counter = field(default_factory=Counter)

    def add(self, kind: str, file_path: Path, line: int, detail: str) -> None:
        self.kind_counter[kind] += 1

    @property
    def score(self) -> int:
        return sum(self.kind_counter.values())


@dataclass(frozen=True, slots=True)
class FileLineInfo:
    relative_path: str
    lines: int
    category: str
    complexity: ComplexityMetrics | None = None
    parse_error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.lines, int) or isinstance(self.lines, bool) or self.lines < 0:
            raise ContractError(f"FileLineInfo.lines must be >= 0, got {self.lines!r}")


@dataclass(frozen=True, slots=True)
class ClassSummary:
    file_path: Path
    class_name: str
    model_names: frozenset[str] = field(default_factory=frozenset)
    declared_models: frozenset[str] = field(default_factory=frozenset)
    inherit_models: frozenset[str] = field(default_factory=frozenset)
    inherit_links: tuple[tuple[str, int], ...] = ()
    declared_methods: frozenset[str] = field(default_factory=frozenset)
    declared_field_models: dict[str, str] = field(default_factory=dict)
    field_models: dict[str, str] = field(default_factory=dict)
    field_links: tuple[tuple[str, str, int, str], ...] = ()
    related_paths: tuple[tuple[str, int, str], ...] = ()
    depends_paths: tuple[tuple[str, int, str], ...] = ()
    onchange_paths: tuple[tuple[str, int, str], ...] = ()
    constrains_paths: tuple[tuple[str, int, str], ...] = ()
    env_accesses: tuple[tuple[str, int], ...] = ()
    method_calls: tuple[tuple[str, str, int], ...] = ()
    field_property_accesses: tuple[tuple[str, str, int], ...] = ()


@dataclass(frozen=True, slots=True)
class ModuleInfo:
    name: str
    path: Path
    manifest_path: Path
    manifest_depends: frozenset[str] = field(default_factory=frozenset)
    declared_models: frozenset[str] = field(default_factory=frozenset)
    inherited_models: frozenset[str] = field(default_factory=frozenset)
    class_summaries: tuple[ClassSummary, ...] = ()
    python_lines: int = 0
    js_lines: int = 0
    python_test_lines: int = 0
    xml_lines: int = 0
    css_lines: int = 0
    html_lines: int = 0
    total_lines: int = 0
    files: tuple[FileLineInfo, ...] = ()
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    python_complexity_files: tuple[FileComplexityInfo, ...] = ()
    python_complexity_parse_errors: int = 0

    def line_categories(self) -> dict[str, int]:
        return {category.value: getattr(self, category.value) for category in LineCategory}


@dataclass(frozen=True, slots=True)
class ModuleFacts:
    name: str
    path: Path
    manifest_path: Path
    manifest_depends: frozenset[str] = field(default_factory=frozenset)
    declared_models: frozenset[str] = field(default_factory=frozenset)
    inherited_models: frozenset[str] = field(default_factory=frozenset)
    class_summaries: tuple[ClassSummary, ...] = ()
    python_lines: int = 0
    js_lines: int = 0
    python_test_lines: int = 0
    xml_lines: int = 0
    css_lines: int = 0
    html_lines: int = 0
    total_lines: int = 0
    files: tuple[FileLineInfo, ...] = ()
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    python_complexity_files: tuple[FileComplexityInfo, ...] = ()
    metrics: dict[str, float] = field(default_factory=dict)
    line_counts: dict[str, int] = field(default_factory=dict)

    def line_categories(self) -> Mapping[str, int]:
        return MappingProxyType(
            {
                "python_lines": self.python_lines,
                "js_lines": self.js_lines,
                "python_test_lines": self.python_test_lines,
                "xml_lines": self.xml_lines,
                "css_lines": self.css_lines,
                "html_lines": self.html_lines,
            }
        )


@dataclass(frozen=True, slots=True)
class LineCategoryCount:
    category: LineCategory
    count: int

    def __post_init__(self) -> None:
        if not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 0:
            raise ContractError(f"LineCategoryCount.count must be >= 0, got {self.count!r}")


@dataclass(frozen=True, slots=True)
class LineCategoryCounts:
    counts: tuple[LineCategoryCount, ...] = ()

    @classmethod
    def empty(cls) -> LineCategoryCounts:
        return cls(counts=tuple(LineCategoryCount(cat, 0) for cat in LineCategory))

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, int]) -> LineCategoryCounts:
        records: list[LineCategoryCount] = []
        for cat in LineCategory:
            records.append(LineCategoryCount(cat, int(mapping.get(cat.value, 0))))
        return cls(counts=tuple(records))

    def count_of(self, category: LineCategory) -> int:
        for record in self.counts:
            if record.category is category:
                return record.count
        return 0

    def total(self) -> int:
        return sum(record.count for record in self.counts)

    def as_mapping(self) -> Mapping[str, int]:
        return MappingProxyType({record.category.value: record.count for record in self.counts})


def freeze_module_info(module: ModuleInfo) -> ModuleFacts:
    return ModuleFacts(
        name=module.name,
        path=module.path,
        manifest_path=module.manifest_path,
        manifest_depends=frozenset(module.manifest_depends),
        declared_models=frozenset(module.declared_models),
        inherited_models=frozenset(module.inherited_models),
        class_summaries=tuple(module.class_summaries),
        python_lines=module.python_lines,
        js_lines=module.js_lines,
        python_test_lines=module.python_test_lines,
        xml_lines=module.xml_lines,
        css_lines=module.css_lines,
        html_lines=module.html_lines,
        total_lines=module.total_lines,
        files=tuple(module.files),
        complexity=module.complexity,
        python_complexity_files=tuple(module.python_complexity_files),
        metrics={
            "python_file_count": len(module.python_complexity_files),
            "cyclomatic_count": module.complexity.cyclomatic.count,
            "cyclomatic_mean": module.complexity.cyclomatic.mean,
            "cyclomatic_median": module.complexity.cyclomatic.median,
            "cyclomatic_p95": module.complexity.cyclomatic.p95,
            "cyclomatic_max": module.complexity.cyclomatic.max,
            "cognitive_count": module.complexity.cognitive.count,
            "cognitive_mean": module.complexity.cognitive.mean,
            "cognitive_median": module.complexity.cognitive.median,
            "cognitive_p95": module.complexity.cognitive.p95,
            "cognitive_max": module.complexity.cognitive.max,
            "jones_count": module.complexity.jones.count,
            "jones_mean": module.complexity.jones.mean,
            "jones_median": module.complexity.jones.median,
            "jones_p95": module.complexity.jones.p95,
            "jones_max": module.complexity.jones.max,
        },
        line_counts={
            "python_lines": module.python_lines,
            "js_lines": module.js_lines,
            "python_test_lines": module.python_test_lines,
            "xml_lines": module.xml_lines,
            "css_lines": module.css_lines,
            "html_lines": module.html_lines,
            "total_lines": module.total_lines,
        },
    )
