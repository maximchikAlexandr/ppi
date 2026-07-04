"""Odoo module discovery: addons path resolution, manifest scanning, filter."""
from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path

from expression.core.result import Error, Ok, Result

from ppi.core.errors import InvalidAddonsPath, ManifestDiscoveryError
from ppi.core.odoo.manifest import ManifestParseFailed, parse_manifest_source
from ppi.core.odoo.scope import (
    AllModules,
    IncludeScope,
    KeepFirst,
    PrefixAndIncludeScope,
    PrefixScope,
    module_scope_of,
    resolve_duplicate_modules,
    select_module_candidates,
)
from ppi.core.odoo.types import AnalysisArtifacts, ModuleInfo, ReportConfig


def build_report_config(
    *,
    project_label: str,
    module_prefixes: tuple[str, ...] = (),
    include_modules: tuple[str, ...] = (),
    all_modules: bool = True,
) -> ReportConfig:
    if all_modules:
        normalized_module_prefixes: tuple[str, ...] = ()
    else:
        normalized_module_prefixes = tuple(sorted(set(module_prefixes)))
    return ReportConfig(
        project_label=project_label,
        module_prefixes=normalized_module_prefixes,
        include_modules=tuple(sorted(set(include_modules))),
        all_modules=all_modules,
    )


def resolve_addons_paths(addons_paths: Iterable[Path]) -> tuple[Path, ...]:
    return tuple(path.resolve() for path in addons_paths)


def validate_addons_paths(
    addons_paths: tuple[Path, ...],
) -> Result[tuple[Path, ...], InvalidAddonsPath]:
    invalid_paths = tuple(str(p) for p in addons_paths if not p.is_dir())
    if invalid_paths:
        return Error(InvalidAddonsPath(paths=invalid_paths))
    return Ok(addons_paths)


def discover_analysis_artifacts(
    config: ReportConfig,
    addons_paths: tuple[Path, ...],
) -> Result[AnalysisArtifacts, ManifestDiscoveryError]:
    modules = discover_modules(list(addons_paths), config)
    if not modules:
        return Error(
            ManifestDiscoveryError(addons_paths=tuple(str(p) for p in addons_paths)),
        )
    return Ok(
        AnalysisArtifacts(
            addons_paths=addons_paths,
            config=config,
            modules=modules,
        ),
    )


def module_matches_filter(module_name: str, config: ReportConfig) -> bool:
    scope = module_scope_of(
        all_modules=config.all_modules,
        module_prefixes=config.module_prefixes,
        include_modules=config.include_modules,
    )
    match scope:
        case AllModules():
            return True
        case PrefixScope() | IncludeScope() | PrefixAndIncludeScope():
            return scope.includes(module_name)
        case _:
            return True


def discover_modules(
    addons_paths: list[Path],
    config: ReportConfig,
) -> dict[str, ModuleInfo]:
    scope = module_scope_of(
        all_modules=config.all_modules,
        module_prefixes=config.module_prefixes,
        include_modules=config.include_modules,
    )

    manifest_paths: list[Path] = []
    for addons_path in addons_paths:
        manifest_paths.extend(sorted(addons_path.rglob("__manifest__.py")))

    candidates = select_module_candidates(tuple(manifest_paths), scope)

    kept_candidates, duplicate_warnings = resolve_duplicate_modules(candidates, KeepFirst())
    for warning in duplicate_warnings:
        print(
            f"[WARN] Duplicate module name {warning.module_name!r}: "
            f"keeping {warning.kept_path}, skipping {warning.skipped_path}",
            file=sys.stderr,
        )

    modules: dict[str, ModuleInfo] = {}
    for candidate in kept_candidates:
        try:
            source = candidate.manifest_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"[WARN] Failed to read {candidate.manifest_path}: {exc}", file=sys.stderr)
            source = ""

        parse_result = parse_manifest_source(source, origin=None)
        if parse_result.is_error():
            failure: ManifestParseFailed = parse_result.error
            print(
                f"[WARN] Failed to parse {candidate.manifest_path}: {failure.message}",
                file=sys.stderr,
            )
            depends: set[str] = set()
        else:
            manifest = parse_result.default_value(None)
            depends = {m.value for m in manifest.depends}

        modules[candidate.module_name] = ModuleInfo(
            name=candidate.module_name,
            path=candidate.module_path,
            manifest_path=candidate.manifest_path,
            manifest_depends=frozenset(depends),
        )

    return modules
