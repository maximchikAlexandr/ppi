"""Module discovery pipeline stages.

Stages:
  - ``discover_modules_stage``: find filtered Odoo modules under addons paths.
  - ``read_manifest_adapter``: read and parse a module manifest file.
  - ``resolve_duplicate_modules_stage``: resolve duplicate module names.
"""

from __future__ import annotations

from pathlib import Path

from expression.core.result import Error, Ok

from ppi.core.odoo.pipeline import (
    ModuleInfo,
    ReportConfig,
    discover_modules,
    resolve_duplicate_modules,
    select_module_candidates,
)
from ppi.core.odoo.scope import KeepFirst, module_scope_of
from ppi.rop.errors import RecoverableDomainFailure, ValidationFailure
from ppi.rop.types import StageResult


def odoo_module_discovery_pipeline(
    addons_paths: list[Path],
    config: ReportConfig,
) -> StageResult[dict[str, ModuleInfo], ValidationFailure]:
    """Spec-named pipeline: discover Odoo modules."""
    return discover_modules_stage(addons_paths, config)


def discover_modules_stage(
    addons_paths: list[Path],
    config: ReportConfig,
) -> StageResult[dict[str, ModuleInfo], ValidationFailure]:
    """Find and filter Odoo modules under the given addons paths."""
    try:
        modules = discover_modules(addons_paths, config)
        if not modules:
            return Error(
                ValidationFailure(
                    stage="discover_modules",
                    message=f"No matching modules found under {addons_paths}",
                    safe_input_id=str(addons_paths),
                )
            )
        return Ok(modules)
    except Exception as exc:
        return Error(
            ValidationFailure(
                stage="discover_modules",
                message=str(exc),
                safe_input_id=str(addons_paths),
                cause=exc,
            )
        )


def read_manifest_adapter(
    manifest_path: Path,
) -> StageResult[str, RecoverableDomainFailure]:
    """Read a manifest file from disk (effect adapter)."""
    try:
        source = manifest_path.read_text(encoding="utf-8", errors="replace")
        return Ok(source)
    except OSError as exc:
        return Error(
            RecoverableDomainFailure(
                stage="read_manifest",
                message=f"Failed to read manifest: {exc}",
                safe_input_id=str(manifest_path),
                cause=exc,
            )
        )


def resolve_duplicate_modules_stage(
    manifest_paths: tuple[Path, ...],
    config: ReportConfig,
) -> StageResult[tuple[Path, ...], RecoverableDomainFailure]:
    """Select and deduplicate module candidates."""
    try:
        scope = module_scope_of(
            all_modules=config.all_modules,
            module_prefixes=config.module_prefixes,
            include_modules=config.include_modules,
        )
        candidates = select_module_candidates(manifest_paths, scope)
        kept, warnings = resolve_duplicate_modules(candidates, KeepFirst())
        return Ok(tuple(c.manifest_path for c in kept))
    except Exception as exc:
        return Error(
            RecoverableDomainFailure(
                stage="resolve_duplicates",
                message=str(exc),
                safe_input_id=str(manifest_paths),
                cause=exc,
            )
        )
