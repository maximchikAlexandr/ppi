"""Odoo module analysis pipeline — re-export hub for backward compat.

All functions and types have been moved to dedicated modules under
``src/ppi/core/odoo/``. This module re-exports them for backward
compatibility. New code should import from the specific modules directly.
"""
from __future__ import annotations

# flake8: noqa: F401

from ppi.core.odoo.class_analysis import (
    MethodAnalyzer,
    analyze_python_file,
    analyze_python_modules,
    build_class_summary,
    get_class_target_models,
)
from ppi.core.odoo.code_metrics import (
    JonesComplexityVisitor,
    analyze_module_code_size,
    analyze_module_code_size_for_module,
    analyze_python_complexity,
    analyze_python_complexity_file,
    analyze_python_complexity_for_module,
    attach_file_complexity_to_line_info,
    build_file_complexity_error_result,
    classify_file,
    collect_cognitive_scores,
    collect_cyclomatic_scores,
    collect_jones_line_scores,
    count_file_lines,
    enrich_modules_with_code_analysis,
    is_test_file,
    iter_radon_function_blocks,
    module_python_file_count,
)
from ppi.core.odoo.discovery import (
    build_report_config,
    discover_analysis_artifacts,
    discover_modules,
    module_matches_filter,
    resolve_addons_paths,
    validate_addons_paths,
)
from ppi.core.odoo.edges import (
    add_manifest_links,
    add_model_links,
    add_module_links,
    analyze_python_links,
    analyze_security_csv,
    analyze_xml_file,
    analyze_xml_links,
    attach_edges_and_scores,
    find_external_ids,
    local_tag_name,
    resolve_related_model,
)
from ppi.core.odoo.providers import (
    attach_provider_maps,
    build_field_providers,
    build_method_providers,
    build_model_owners,
)
from ppi.core.odoo.dist_stats import build_distribution_stats
from ppi.core.odoo.types import (
    AnalysisArtifacts,
    ClassSummary,
    CouplingEdgeAccumulator,
    FileLineInfo,
    ModuleInfo,
    ReportConfig,
)
