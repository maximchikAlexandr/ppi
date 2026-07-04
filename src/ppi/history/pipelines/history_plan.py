"""Pure history plan stage.

Builds the commit selection plan from repository metadata without
side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CommitPlanEntry:
    """One commit to process in the history walk."""
    commit_hash: str
    commit_order: int


@dataclass(frozen=True, slots=True)
class HistoryPlan:
    """Ordered list of commits to walk through."""
    commits: tuple[CommitPlanEntry, ...] = ()


def history_plan_pipeline(
    raw_log: str,
    limit: int = 100,
) -> HistoryPlan:
    """Spec-named pipeline: build history plan from raw log."""
    return build_history_plan(raw_log, limit)


def build_history_plan(
    raw_log: str,
    limit: int = 100,
) -> HistoryPlan:
    """Build a commit plan from raw git log output (pure).

    Parses each log line as ``<hash> <timestamp> <subject>`` and
    returns the ordered commit plan.
    """
    entries: list[CommitPlanEntry] = []
    for i, line in enumerate(raw_log.strip().split("\n")):
        if not line.strip() or i >= limit:
            break
        parts = line.split(" ", 1)
        if parts:
            entries.append(
                CommitPlanEntry(
                    commit_hash=parts[0],
                    commit_order=i,
                )
            )
    return HistoryPlan(commits=tuple(entries))
