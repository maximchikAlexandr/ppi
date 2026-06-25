"""Typed edge scoring via ``match EdgeKindGroup`` (no ``if`` chains).

Replaces the legacy ``edge_breakdown`` that summed over stringly kind sets with
a declarative group dispatch over the typed :class:`EdgeKind` enum. Scoring is
pure: input is an iterable of typed kind counts, output is an immutable
:class:`EdgeBreakdown` (re-using the typed version from :mod:`ppi.core.odoo.facts`
to avoid a second type).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from ppi.core.odoo.facts import EdgeBreakdown, EdgeKindCount
from ppi.core.value_objects import EdgeKind, EdgeKindGroup, edge_kind_group_of

__all__ = [
    "score_from_kind_counts",
    "score_from_kinds",
    "breakdown_from_kind_counts",
    "module_scores_from_edges",
]


def breakdown_from_kind_counts(counts: Iterable[EdgeKindCount]) -> EdgeBreakdown:
    """Build a typed breakdown from typed kind counts via ``match`` group dispatch."""
    model_reuse = 0
    extension_or_method = 0
    view = 0
    field_property = 0
    for record in counts:
        match edge_kind_group_of(record.kind):
            case EdgeKindGroup.MODEL_REUSE:
                model_reuse += record.count
            case EdgeKindGroup.EXTENSION_OR_METHOD:
                extension_or_method += record.count
            case EdgeKindGroup.VIEW:
                view += record.count
            case EdgeKindGroup.FIELD_PROPERTY:
                field_property += record.count
    return EdgeBreakdown(
        model_reuse=model_reuse,
        extension_or_method=extension_or_method,
        view=view,
        field_property=field_property,
    )


def score_from_kind_counts(counts: Iterable[EdgeKindCount]) -> int:
    """Return the total graph points for typed kind counts."""
    return breakdown_from_kind_counts(counts).total


def score_from_kinds(kinds: Iterable[EdgeKind]) -> int:
    """Return the total graph points for an iterable of (unaggregated) kinds."""
    counter: Counter[EdgeKind] = Counter()
    for kind in kinds:
        counter[kind] += 1
    counts = tuple(EdgeKindCount(kind=k, count=c) for k, c in counter.items())
    return score_from_kind_counts(counts)


def module_scores_from_edges(
    module_names: Iterable[str],
    edges: Iterable[tuple[str, str, int]],
) -> dict[str, dict[str, int]]:
    """Build per-module ``{outgoing_score, incoming_score}`` from ``(src, tgt, score)``.

    Pure: input is already-aggregated edge triples; no mutation of edges.
    """
    stats: dict[str, dict[str, int]] = {
        name: {"outgoing_score": 0, "incoming_score": 0} for name in module_names
    }
    for source, target, score_value in edges:
        if score_value <= 0:
            continue
        if source in stats:
            stats[source]["outgoing_score"] += score_value
        if target in stats:
            stats[target]["incoming_score"] += score_value
    return stats
