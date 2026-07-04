"""Module scope discriminated union and duplicate resolution (PPI-004/PPI-010).

Extracted from ``snapshots.py`` to eliminate that module's "kitchen sink"
responsibility. All types here are pure dataclasses/functions with no
dependencies on other ``ppi.core.odoo`` modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ppi.core.value_objects import ContractError

__all__ = [
    "AllModules",
    "PrefixScope",
    "IncludeScope",
    "PrefixAndIncludeScope",
    "ModuleScope",
    "module_scope_of",
    "DuplicatePolicy",
    "KeepFirst",
    "PreferPath",
    "FailOnDuplicate",
    "DuplicateModuleWarning",
    "ModuleCandidate",
    "select_module_candidates",
    "resolve_duplicate_modules",
]


# --- Module scope discriminated union ----------------------------------------


@dataclass(frozen=True, slots=True)
class AllModules:
    """Scope: include every module."""

    def includes(self, module_name: str) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class PrefixScope:
    """Scope: modules whose name starts with any of the prefixes."""

    prefixes: tuple[str, ...] = ()

    def includes(self, module_name: str) -> bool:
        return any(module_name.startswith(prefix) for prefix in self.prefixes)


@dataclass(frozen=True, slots=True)
class IncludeScope:
    """Scope: only explicitly listed modules."""

    include: frozenset[str] = field(default_factory=frozenset)

    def includes(self, module_name: str) -> bool:
        return module_name in self.include


@dataclass(frozen=True, slots=True)
class PrefixAndIncludeScope:
    """Scope: modules matching a prefix OR explicitly listed."""

    prefixes: tuple[str, ...] = ()
    include: frozenset[str] = field(default_factory=frozenset)

    def includes(self, module_name: str) -> bool:
        if module_name in self.include:
            return True
        return any(module_name.startswith(prefix) for prefix in self.prefixes)


ModuleScope = AllModules | PrefixScope | IncludeScope | PrefixAndIncludeScope


def module_scope_of(
    *,
    all_modules: bool,
    module_prefixes: tuple[str, ...] = (),
    include_modules: tuple[str, ...] = (),
) -> ModuleScope:
    prefixes = tuple(sorted(set(module_prefixes)))
    include = frozenset(include_modules)
    if all_modules:
        return AllModules()
    if prefixes and include:
        return PrefixAndIncludeScope(prefixes=prefixes, include=include)
    if prefixes:
        return PrefixScope(prefixes=prefixes)
    if include:
        return IncludeScope(include=include)
    return AllModules()


# --- Duplicate module resolution types --------------------------------------


@dataclass(frozen=True, slots=True)
class KeepFirst:
    """Duplicate policy: keep the first-seen module, skip later ones."""


@dataclass(frozen=True, slots=True)
class PreferPath:
    """Duplicate policy: prefer the module at the given path prefix."""

    preferred_prefix: str


@dataclass(frozen=True, slots=True)
class FailOnDuplicate:
    """Duplicate policy: fail when a duplicate module name is seen."""


DuplicatePolicy = KeepFirst | PreferPath | FailOnDuplicate


@dataclass(frozen=True, slots=True)
class DuplicateModuleWarning:
    """One duplicate-module resolution warning (non-fatal)."""

    module_name: str
    kept_path: str
    skipped_path: str


# --- Module candidate & selection -------------------------------------------


@dataclass(frozen=True, slots=True)
class ModuleCandidate:
    """One candidate module discovered from a manifest path."""

    module_name: str
    module_path: Path
    manifest_path: Path


def select_module_candidates(
    manifest_paths: tuple[Path, ...],
    scope: ModuleScope,
) -> tuple[ModuleCandidate, ...]:
    out: list[ModuleCandidate] = []
    for manifest_path in manifest_paths:
        module_path = manifest_path.parent
        module_name = module_path.name
        if not scope.includes(module_name):
            continue
        out.append(
            ModuleCandidate(
                module_name=module_name,
                module_path=module_path,
                manifest_path=manifest_path,
            ),
        )
    return tuple(out)


def resolve_duplicate_modules(
    candidates: tuple[ModuleCandidate, ...],
    policy: DuplicatePolicy,
) -> tuple[tuple[ModuleCandidate, ...], tuple[DuplicateModuleWarning, ...]]:
    seen: dict[str, ModuleCandidate] = {}
    warnings: list[DuplicateModuleWarning] = []
    kept_order: list[ModuleCandidate] = []
    for candidate in candidates:
        name = candidate.module_name
        if name not in seen:
            seen[name] = candidate
            kept_order.append(candidate)
            continue
        existing = seen[name]
        match policy:
            case KeepFirst():
                warnings.append(
                    DuplicateModuleWarning(
                        module_name=name,
                        kept_path=str(existing.module_path),
                        skipped_path=str(candidate.module_path),
                    ),
                )
            case PreferPath(preferred_prefix=prefix):
                if str(candidate.module_path).startswith(prefix) and not str(
                    existing.module_path,
                ).startswith(prefix):
                    seen[name] = candidate
                    kept_order = [candidate if c.module_name == name else c for c in kept_order]
                    warnings.append(
                        DuplicateModuleWarning(
                            module_name=name,
                            kept_path=str(candidate.module_path),
                            skipped_path=str(existing.module_path),
                        ),
                    )
                else:
                    warnings.append(
                        DuplicateModuleWarning(
                            module_name=name,
                            kept_path=str(existing.module_path),
                            skipped_path=str(candidate.module_path),
                        ),
                    )
            case FailOnDuplicate():
                raise ContractError(
                    f"Duplicate module name {name!r}: "
                    f"{existing.module_path} and {candidate.module_path}",
                )
    return tuple(kept_order), tuple(warnings)
