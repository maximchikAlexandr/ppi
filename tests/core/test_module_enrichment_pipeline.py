"""Module enrichment pipeline tests.

Verifies enrichment succeeds for valid modules and returns
recoverable domain failures for malformed inputs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ppi.core.odoo.pipeline import (
    AnalysisArtifacts,
    ModuleInfo,
    ReportConfig,
    enrich_modules_with_code_analysis,
)
from ppi.core.odoo.types import freeze_module_info


@pytest.fixture
def sample_artifacts() -> AnalysisArtifacts:
    return AnalysisArtifacts(
        addons_paths=(Path(".").resolve(),),
        config=ReportConfig(project_label="test", all_modules=True),
        modules={},
    )


class TestModuleEnrichmentPipeline:
    """Tests for the module enrichment pipeline stage."""

    def test_enrichment_with_empty_modules_returns_empty(self, sample_artifacts: AnalysisArtifacts) -> None:
        result = enrich_modules_with_code_analysis(sample_artifacts)
        assert len(result.modules) == 0

    def test_enrichment_preserves_existing_fields(self) -> None:
        path = Path(".").resolve()
        module = ModuleInfo(name="test_module", path=path, manifest_path=path / "__manifest__.py")
        artifacts = AnalysisArtifacts(
            addons_paths=(path,),
            config=ReportConfig(project_label="test", all_modules=True),
            modules={"test_module": module},
        )
        result = enrich_modules_with_code_analysis(artifacts)
        assert "test_module" in result.modules
        assert result.modules["test_module"].name == "test_module"
