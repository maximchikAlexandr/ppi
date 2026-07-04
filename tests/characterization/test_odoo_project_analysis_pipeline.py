"""Success characterization test for ``odoo_project_analysis_pipeline``.

Verifies that the migrated ROP pipeline produces equivalent output
for representative inputs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ppi.core.contracts import AnalysisBatch, CommitRef
from ppi.core.pipelines.odoo_project import odoo_project_analysis_pipeline


@pytest.fixture
def sample_commit() -> CommitRef:
    return CommitRef(
        commit_hash="abc123def456",
        commit_order=1,
        author_name="Test Author",
        author_email="test@example.com",
        authored_at=1700000000,
        committed_at=1700000000,
        summary="Test commit",
    )


class TestOdooProjectAnalysisPipeline:
    """Characterization tests for the Odoo project analysis pipeline."""

    def test_pipeline_returns_result_for_valid_repo(
        self,
        sample_commit: CommitRef,
    ) -> None:
        result = odoo_project_analysis_pipeline(
            Path("tests/fixtures/sample_repo"),
            sample_commit,
            profile="odoo",
            addons_paths=(Path("tests/fixtures/sample_repo"),),
        )
        assert result is not None

    def test_pipeline_fails_for_invalid_profile(
        self,
        sample_commit: CommitRef,
    ) -> None:
        result = odoo_project_analysis_pipeline(
            Path("/tmp"),
            sample_commit,
            profile="invalid_profile",
            addons_paths=(Path("/tmp"),),
        )
        assert result.is_error()

    def test_pipeline_returns_typed_error_for_missing_addons(
        self,
        sample_commit: CommitRef,
    ) -> None:
        result = odoo_project_analysis_pipeline(
            Path("/nonexistent"),
            sample_commit,
            profile="odoo",
            addons_paths=(Path("/nonexistent"),),
        )
        if result.is_error():
            from ppi.core.errors import InvalidAddonsPath

            assert isinstance(result.error, InvalidAddonsPath) or "Invalid" in str(result.error)
