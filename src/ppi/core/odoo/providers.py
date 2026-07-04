"""Odoo provider index: model_owners, field_providers, method_providers."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from ppi.core.odoo.class_analysis import get_class_target_models
from ppi.core.odoo.types import AnalysisArtifacts, ModuleInfo


def build_model_owners(modules: dict[str, ModuleInfo]) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = defaultdict(set)
    for module in modules.values():
        for model_name in module.declared_models:
            owners[model_name].add(module.name)
    return owners


def build_field_providers(
    modules: dict[str, ModuleInfo],
) -> dict[tuple[str, str], set[str]]:
    providers: dict[tuple[str, str], set[str]] = defaultdict(set)
    for module in modules.values():
        for class_summary in module.class_summaries:
            target_models = get_class_target_models(class_summary)
            for model_name in target_models:
                for field_name in class_summary.declared_field_models:
                    providers[(model_name, field_name)].add(module.name)
    return providers


def build_method_providers(
    modules: dict[str, ModuleInfo],
) -> dict[tuple[str, str], set[str]]:
    providers: dict[tuple[str, str], set[str]] = defaultdict(set)
    for module in modules.values():
        for class_summary in module.class_summaries:
            target_models = get_class_target_models(class_summary)
            for model_name in target_models:
                for method_name in class_summary.declared_methods:
                    providers[(model_name, method_name)].add(module.name)
    return providers


def attach_provider_maps(artifacts: AnalysisArtifacts) -> AnalysisArtifacts:
    return replace(
        artifacts,
        model_owners=build_model_owners(artifacts.modules),
        field_providers=build_field_providers(artifacts.modules),
        method_providers=build_method_providers(artifacts.modules),
    )
