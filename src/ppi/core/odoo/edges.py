"""Odoo coupling edge detection: manifest, Python analysis, XML/CSV analysis."""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree

from ppi.core.odoo.edge_scoring import module_scores_from_edges
from ppi.core.odoo.facts import EdgeFact, reduce_edge_facts
from ppi.core.odoo.types import (
    AnalysisArtifacts,
    CouplingEdgeAccumulator,
    ModuleInfo,
)
from ppi.core.value_objects import EdgeKind, edge_kind_of
from ppi.core.value_objects import ModuleName as _ModuleName

EXTERNAL_ID_RE = re.compile(r"([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)")
PERCENT_EXTERNAL_ID_RE = re.compile(r"%\(([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)\)d")


def local_tag_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def find_external_ids(text: str) -> list[str]:
    return [match.group(1) for match in EXTERNAL_ID_RE.finditer(text)]


def resolve_related_model(path: str, field_models: dict[str, str]) -> str | None:
    root_field = path.split(".", 1)[0]
    return field_models.get(root_field)


def _ensure_edge(
    edges: dict[tuple[str, str], CouplingEdgeAccumulator],
    source_module: str,
    target_module: str,
) -> CouplingEdgeAccumulator:
    return edges.setdefault(
        (source_module, target_module),
        CouplingEdgeAccumulator(source_module=source_module, target_module=target_module),
    )


def _resolve_line_in_text(
    text: str,
    snippet: str,
    snippet_offsets: dict[str, int],
    fallback_line: int = 0,
) -> int:
    if not snippet:
        return fallback_line
    start = snippet_offsets.get(snippet, 0)
    index = text.find(snippet, start)
    if index == -1:
        index = text.find(snippet)
        if index == -1:
            return fallback_line
    snippet_offsets[snippet] = index + len(snippet)
    return text.count("\n", 0, index) + 1


def add_model_links(
    edges: dict[tuple[str, str], CouplingEdgeAccumulator],
    modules: dict[str, ModuleInfo],
    model_owners: dict[str, set[str]],
    source_module: str,
    model_name: str,
    kind: str,
    file_path: Path,
    line: int,
    detail: str,
) -> None:
    for target_module in sorted(model_owners.get(model_name, set())):
        if target_module == source_module or target_module not in modules:
            continue
        _ensure_edge(edges, source_module, target_module).add(
            kind=kind, file_path=file_path, line=line, detail=detail,
        )


def add_module_links(
    edges: dict[tuple[str, str], CouplingEdgeAccumulator],
    modules: dict[str, ModuleInfo],
    source_module: str,
    target_modules: set[str],
    kind: str,
    file_path: Path,
    line: int,
    detail: str,
) -> None:
    for target_module in sorted(target_modules):
        if target_module == source_module or target_module not in modules:
            continue
        _ensure_edge(edges, source_module, target_module).add(
            kind=kind, file_path=file_path, line=line, detail=detail,
        )


def add_manifest_links(
    modules: dict[str, ModuleInfo],
    edges: dict[tuple[str, str], CouplingEdgeAccumulator],
) -> None:
    for module in modules.values():
        for dependency in sorted(module.manifest_depends):
            if dependency == module.name or dependency not in modules:
                continue
            _ensure_edge(edges, module.name, dependency).add(
                kind=EdgeKind.MANIFEST_DEPENDS.value,
                file_path=module.manifest_path,
                line=0,
                detail=f"depends -> {dependency}",
            )


def analyze_python_links(
    modules: dict[str, ModuleInfo],
    model_owners: dict[str, set[str]],
    field_providers: dict[tuple[str, str], set[str]],
    method_providers: dict[tuple[str, str], set[str]],
    edges: dict[tuple[str, str], CouplingEdgeAccumulator],
) -> None:
    for module in modules.values():
        for cs in module.class_summaries:

            def ml(*, model_name, kind, line, detail):
                add_model_links(edges=edges, modules=modules, model_owners=model_owners,
                                source_module=module.name, model_name=model_name,
                                kind=kind, file_path=cs.file_path, line=line, detail=detail)

            for inherited_model, inherit_line in cs.inherit_links:
                ml(model_name=inherited_model, kind=EdgeKind.PYTHON_INHERIT.value,
                   line=inherit_line, detail=f"_inherit -> {inherited_model}")

            for kind, comodel_name, line, detail in cs.field_links:
                ml(model_name=comodel_name, kind=kind, line=line, detail=detail)

            for related_path, line, field_name in cs.related_paths:
                model_name = resolve_related_model(related_path, cs.field_models)
                if model_name:
                    ml(model_name=model_name, kind=EdgeKind.PYTHON_RELATED.value,
                       line=line, detail=f"related={related_path} ({field_name})")

            for attr_name, edge_kind in (
                ("depends", EdgeKind.PYTHON_API_DEPENDS.value),
                ("onchange", EdgeKind.PYTHON_API_ONCHANGE.value),
                ("constrains", EdgeKind.PYTHON_API_CONSTRAINS.value),
            ):
                for path_value, line, method_name in getattr(cs, f"{attr_name}_paths"):
                    model_name = resolve_related_model(path_value, cs.field_models)
                    if model_name:
                        ml(model_name=model_name, kind=edge_kind, line=line,
                           detail=f"@api.{attr_name}('{path_value}') in {method_name}")

            for model_name, line in cs.env_accesses:
                ml(model_name=model_name, kind=EdgeKind.PYTHON_ENV_MODEL.value,
                   line=line, detail=f"self.env['{model_name}'] access")

            for model_name, method_name, line in cs.method_calls:
                kind = (
                    EdgeKind.PYTHON_PRIVATE_METHOD_CALL.value
                    if method_name.startswith("_")
                    else EdgeKind.PYTHON_METHOD_CALL.value
                )
                providers = method_providers.get((model_name, method_name), set())
                add_module_links(edges=edges, modules=modules,
                                 source_module=module.name, target_modules=providers,
                                 kind=kind, file_path=cs.file_path, line=line,
                                 detail=f"{model_name}.{method_name}()")

            for model_name, field_name, line in cs.field_property_accesses:
                providers = field_providers.get((model_name, field_name), set())
                add_module_links(edges=edges, modules=modules,
                                 source_module=module.name, target_modules=providers,
                                 kind=EdgeKind.PYTHON_FIELD_PROPERTY_ACCESS.value,
                                 file_path=cs.file_path, line=line,
                                 detail=f"{model_name}.{field_name} access")


def analyze_xml_file(
    file_path: Path,
    source_module: str,
    modules: dict[str, ModuleInfo],
    edges: dict[tuple[str, str], CouplingEdgeAccumulator],
) -> None:
    text = file_path.read_text(encoding="utf-8")
    security_file = "security" in file_path.parts
    snippet_offsets: dict[str, int] = defaultdict(int)

    def resolve_line(snippet: str, fallback_line: int = 0) -> int:
        return _resolve_line_in_text(text, snippet, snippet_offsets, fallback_line)

    for match in PERCENT_EXTERNAL_ID_RE.finditer(text):
        xml_id = match.group(1)
        target_module = xml_id.split(".", 1)[0]
        if target_module == source_module or target_module not in modules:
            continue
        line = text.count("\n", 0, match.start()) + 1
        _ensure_edge(edges, source_module, target_module).add(
            kind=EdgeKind.XML_PERCENT_REF.value,
            file_path=file_path, line=line, detail=f"%({xml_id})d",
        )

    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        print(f"[WARN] Invalid XML {file_path}: {exc}", file=sys.stderr)
        return

    def traverse(element: ElementTree.Element, record_model: str | None = None) -> None:
        current_record_model = record_model
        if local_tag_name(element.tag) == "record":
            current_record_model = element.attrib.get("model")

        if local_tag_name(element.tag) == "field":
            field_name = element.attrib.get("name")
            field_ref = element.attrib.get("ref")
            field_text = (element.text or "").strip()
            xml_id = field_ref or field_text
            line = getattr(element, "sourceline", 0) or 0

            if field_name == "inherit_id" and "." in xml_id:
                target_module = xml_id.split(".", 1)[0]
                if target_module != source_module and target_module in modules:
                    _ensure_edge(edges, source_module, target_module).add(
                        kind=EdgeKind.XML_INHERIT_ID.value,
                        file_path=file_path, line=resolve_line(xml_id, line),
                        detail=f"inherit_id -> {xml_id}",
                    )

            if current_record_model == "ir.rule" and field_name == "model_id" and "." in xml_id:
                target_module = xml_id.split(".", 1)[0]
                if target_module != source_module and target_module in modules:
                    _ensure_edge(edges, source_module, target_module).add(
                        kind=EdgeKind.SECURITY_IR_RULE_MODEL_REF.value,
                        file_path=file_path, line=resolve_line(xml_id, line),
                        detail=f"ir.rule model_id -> {xml_id}",
                    )

        ref_value = element.attrib.get("ref")
        if ref_value and "." in ref_value:
            target_module = ref_value.split(".", 1)[0]
            if target_module != source_module and target_module in modules:
                if current_record_model == "ir.rule":
                    kind = EdgeKind.SECURITY_IR_RULE_REF.value
                elif security_file:
                    kind = EdgeKind.SECURITY_XML_REF.value
                else:
                    kind = EdgeKind.XML_REF.value
                _ensure_edge(edges, source_module, target_module).add(
                    kind=kind, file_path=file_path,
                    line=resolve_line(ref_value, getattr(element, "sourceline", 0) or 0),
                    detail=f"ref -> {ref_value}",
                )

        for child in element:
            traverse(child, current_record_model)

    traverse(root)


def analyze_security_csv(
    file_path: Path,
    source_module: str,
    modules: dict[str, ModuleInfo],
    edges: dict[tuple[str, str], CouplingEdgeAccumulator],
) -> None:
    with file_path.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        for row_index, row in enumerate(reader, start=2):
            for value in row.values():
                if not value:
                    continue
                for xml_id in find_external_ids(value):
                    target_module = xml_id.split(".", 1)[0]
                    if target_module == source_module or target_module not in modules:
                        continue
                    _ensure_edge(edges, source_module, target_module).add(
                        kind=EdgeKind.SECURITY_CSV_REF.value,
                        file_path=file_path, line=row_index,
                        detail=f"security csv ref -> {xml_id}",
                    )


def analyze_xml_links(
    modules: dict[str, ModuleInfo],
    edges: dict[tuple[str, str], CouplingEdgeAccumulator],
) -> None:
    for module in modules.values():
        for xml_path in sorted(module.path.rglob("*.xml")):
            try:
                analyze_xml_file(
                    file_path=xml_path, source_module=module.name,
                    modules=modules, edges=edges,
                )
            except UnicodeDecodeError as exc:
                print(f"[WARN] Cannot decode XML {xml_path}: {exc}", file=sys.stderr)

        security_dir = module.path / "security"
        if not security_dir.exists():
            continue
        for csv_path in sorted(security_dir.rglob("*.csv")):
            try:
                analyze_security_csv(
                    file_path=csv_path, source_module=module.name,
                    modules=modules, edges=edges,
                )
            except UnicodeDecodeError as exc:
                print(f"[WARN] Cannot decode CSV {csv_path}: {exc}", file=sys.stderr)


def _accumulators_to_edge_facts(
    edges: dict[tuple[str, str], CouplingEdgeAccumulator],
) -> tuple[EdgeFact, ...]:
    out: list[EdgeFact] = []
    for edge in edges.values():
        src = _ModuleName.parse(edge.source_module)
        tgt = _ModuleName.parse(edge.target_module)
        if src is None or tgt is None:
            continue
        for kind_str in edge.kind_counter:
            kind_typed = edge_kind_of(kind_str)
            if kind_typed is None:
                continue
            out.append(EdgeFact(source_module=src, target_module=tgt, kind=kind_typed))
    return tuple(out)


def attach_edges_and_scores(artifacts: AnalysisArtifacts) -> AnalysisArtifacts:
    edges: dict[tuple[str, str], CouplingEdgeAccumulator] = {}
    add_manifest_links(artifacts.modules, edges)
    analyze_python_links(
        modules=artifacts.modules, model_owners=artifacts.model_owners,
        field_providers=artifacts.field_providers,
        method_providers=artifacts.method_providers, edges=edges,
    )
    analyze_xml_links(artifacts.modules, edges)

    facts = _accumulators_to_edge_facts(edges)
    snapshots = reduce_edge_facts(facts)
    score_triples = tuple(
        (s.source_module.value, s.target_module.value, s.score) for s in snapshots
    )
    module_scores = module_scores_from_edges(artifacts.modules.keys(), score_triples)
    return replace(
        artifacts,
        edge_snapshots=snapshots,
        module_scores=module_scores,
    )
