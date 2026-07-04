"""Addons path resolution and validation stages.

Stages:
  - ``resolve_addons_paths_stage``: resolve all incoming addons paths to absolute.
  - ``validate_addons_paths_stage``: validate every path is an existing directory.
"""

from __future__ import annotations

from pathlib import Path

from expression.core.result import Error, Ok

from ppi.core.odoo.pipeline import resolve_addons_paths, validate_addons_paths
from ppi.rop.errors import ValidationFailure
from ppi.rop.types import StageResult


def addons_path_validation_pipeline(
    addons_paths: tuple[Path, ...],
) -> StageResult[tuple[Path, ...], ValidationFailure]:
    """Spec-named pipeline: resolve and validate addons paths."""
    resolved = resolve_addons_paths_stage(addons_paths)
    return validate_addons_paths_stage(resolved)


def resolve_addons_paths_stage(
    addons_paths: tuple[Path, ...],
) -> tuple[Path, ...]:
    """Resolve addons paths to absolute form (pure, infallible)."""
    return resolve_addons_paths(addons_paths)


def validate_addons_paths_stage(
    addons_paths: tuple[Path, ...],
) -> StageResult[tuple[Path, ...], ValidationFailure]:
    """Validate that every addons path is an existing directory.

    Returns ``Error(ValidationFailure)`` instead of raising ValueError.
    """
    validated = validate_addons_paths(addons_paths)
    if validated.is_error():
        return Error(
            ValidationFailure(
                stage="validate_addons_paths",
                message=str(validated.error),
                safe_input_id=str(addons_paths),
            )
        )
    return Ok(validated.default_value(None))
