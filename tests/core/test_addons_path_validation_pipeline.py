"""Tests for addons path validation in the ROP pipeline.

Verifies that invalid paths return typed ``ValidationFailure`` instead
of raising exceptions.
"""

from __future__ import annotations

from pathlib import Path

from ppi.core.pipelines.addons_paths import (
    validate_addons_paths_stage,
)
from ppi.rop.errors import ValidationFailure


class TestAddonsPathValidationPipeline:
    """Tests for the addons path validation ROP stage."""

    def test_valid_paths_return_ok(self) -> None:
        existing = Path(".").resolve()
        result = validate_addons_paths_stage((existing,))
        assert result.is_ok()
        assert existing in result.default_value(None)

    def test_invalid_path_returns_validation_failure(self) -> None:
        result = validate_addons_paths_stage((Path("/nonexistent/path"),))
        assert result.is_error()
        assert isinstance(result.error, ValidationFailure)
        assert "validate_addons_paths" in result.error.stage

    def test_mixed_paths_reports_invalid(self) -> None:
        existing = Path(".").resolve()
        result = validate_addons_paths_stage((existing, Path("/nonexistent")))
        assert result.is_error()
        assert isinstance(result.error, ValidationFailure)
