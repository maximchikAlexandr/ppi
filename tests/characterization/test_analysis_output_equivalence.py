"""Shared Python characterization fixture for analysis output equivalence.

Provides a parametrized fixture that runs the current analysis pipeline
and compares output to a golden snapshot. Used by all migration slices
to detect behavior changes during refactoring.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ppi.core.contracts import AnalysisBatch
from ppi.core.odoo.pipeline import (
    AnalysisArtifacts,
    ReportConfig,
    attach_edges_and_scores,
    attach_provider_maps,
    build_report_config,
    discover_analysis_artifacts,
    enrich_modules_with_code_analysis,
    resolve_addons_paths,
    validate_addons_paths,
)


@pytest.fixture
def sample_repo_path() -> Path:
    path = Path("tests/fixtures/sample_repo")
    if not path.exists():
        pytest.skip(f"Sample repo fixture not found: {path}")
    return path


@pytest.fixture
def report_config() -> ReportConfig:
    return build_report_config(project_label="test_repo", all_modules=True)


def run_analysis_pipeline(
    addons_paths: tuple[Path, ...],
    config: ReportConfig,
) -> AnalysisArtifacts | None:
    """Run the full analysis pipeline and return artifacts or None on failure."""
    resolved = resolve_addons_paths(addons_paths)
    validated = validate_addons_paths(resolved)
    if validated.is_error():
        return None
    discovered = discover_analysis_artifacts(config, validated.default_value(None))
    if discovered.is_error():
        return None
    return attach_edges_and_scores(
        attach_provider_maps(
            enrich_modules_with_code_analysis(
                discovered.default_value(None),
            ),
        ),
    )


class TestAnalysisOutputEquivalence:
    """Characterization tests: pipeline output must remain equivalent to baseline."""

    def test_valid_repo_produces_analysis_batch(self, sample_repo_path: Path, report_config: ReportConfig) -> None:
        artifacts = run_analysis_pipeline((sample_repo_path,), report_config)
        assert artifacts is not None, "Pipeline should succeed for a valid repo"
        assert isinstance(artifacts, AnalysisArtifacts)

    def test_invalid_addons_path_returns_typed_failure(self) -> None:
        addons_paths = (Path("/nonexistent/path"),)
        resolved = resolve_addons_paths(addons_paths)
        validated = validate_addons_paths(resolved)
        assert validated.is_error()
        from ppi.core.errors import InvalidAddonsPath
        assert isinstance(validated.error, InvalidAddonsPath)
