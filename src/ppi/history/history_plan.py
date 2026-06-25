"""History traversal plan value objects (PPI-018/PPI-050).

The walk is modelled as an immutable plan of commit hashes; the runner
(:func:`ppi.history.walker.walk_history`) stays an imperative generator that
calls effect handlers. The plan types make the commit list/skip set testable
without git checkout or analysis.

``AddonsScanRoots`` (PPI-051) turns the worktree-containment guard into an
explicit domain invariant instead of a scattered ``if``.

The earlier state-machine layer (``HistoryState``/``HistoryEvent``/
``HistoryStep``/``next_history_step``/``iter_history_events``) was removed
because the runner never consumed it — it was an abstraction without a second
production caller (F7). The plan itself stays because the walker uses it.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from expression.core.result import Error, Ok, Result

from ppi.history.value_objects import AddonsPath, WorktreePath

__all__ = [
    "AddonsScanRoots",
    "HistoryPlan",
    "build_history_plan",
]


@dataclass(frozen=True, slots=True)
class AddonsScanRoots:
    """Addon scan roots guaranteed to stay inside a worktree (PPI-051).

    Construction validates containment: every root either equals the worktree
    or is a descendant of it. Violations are returned as a typed ``Error``
    rather than raised from the factory, since this is a recoverable
    user/CLI-input error.
    """

    worktree: WorktreePath
    roots: tuple[AddonsPath, ...]

    @classmethod
    def empty(cls, worktree: WorktreePath) -> AddonsScanRoots:
        """Build scan roots consisting of only the worktree itself."""
        return cls(worktree=worktree, roots=(AddonsPath.of(worktree.value),))

    @classmethod
    def from_cli(
        cls,
        worktree_path: Path,
        addons_paths: Iterable[str],
    ) -> Result[AddonsScanRoots, str]:
        """Resolve addon scan roots and ensure they stay inside the worktree."""
        worktree_resolved = worktree_path.resolve()
        worktree_vo = WorktreePath.of(str(worktree_resolved))
        subpaths = list(addons_paths)
        if not subpaths:
            return Ok(cls.empty(worktree_vo))
        roots: list[AddonsPath] = []
        for subpath in subpaths:
            candidate = Path(subpath)
            resolved = (
                candidate.resolve()
                if candidate.is_absolute()
                else (worktree_resolved / candidate).resolve()
            )
            if resolved != worktree_resolved and worktree_resolved not in resolved.parents:
                return Error(f"addons path must stay inside worktree: {subpath}")
            roots.append(AddonsPath.of(str(resolved)))
        return Ok(cls(worktree=worktree_vo, roots=tuple(roots)))

    def as_paths(self) -> tuple[Path, ...]:
        """Return roots as ``Path`` objects for adapter callers."""
        return tuple(Path(r.value) for r in self.roots)


@dataclass(frozen=True, slots=True)
class HistoryPlan:
    """Immutable plan for one history walk.

    ``commits`` is the ordered list of commit hashes to walk; ``order_by_hash``
    maps each hash to its position. Effect handlers are supplied by the runner.
    """

    commits: tuple[str, ...]
    order_by_hash: dict[str, int] = field(default_factory=dict)
    scan_roots: AddonsScanRoots | None = None
    profile: str = "odoo"


def build_history_plan(
    commits: list[str],
    *,
    scan_roots: AddonsScanRoots | None = None,
    skip: set[str] | None = None,
    profile: str = "odoo",
) -> HistoryPlan:
    """Build an immutable history plan from a commit list (pure)."""
    skip_set = skip or set()
    filtered = [c for c in commits if c not in skip_set]
    order_by_hash = {c: i for i, c in enumerate(commits)}
    return HistoryPlan(
        commits=tuple(filtered),
        order_by_hash=order_by_hash,
        scan_roots=scan_roots,
        profile=profile,
    )
