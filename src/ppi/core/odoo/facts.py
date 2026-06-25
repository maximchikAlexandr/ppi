"""Immutable coupling-edge value objects (facts and snapshots).

The graph is built as a pure pipeline:

    EdgeFact[] -> reduce_edge_facts -> CouplingEdgeSnapshot[]

:class:`EdgeFact` carries only data — it never reads files. Source-quote
enrichment happens in the adapter (see
:class:`ppi.adapters.filesystem.FilesystemSourceQuoteProvider`) before a fact
is constructed, or in a separate enrichment phase.

This module is the typed replacement for the mutable
:class:`ppi.core.odoo.pipeline.CouplingEdgeAccumulator` flow. The accumulator
stays as an internal builder, but public results are immutable snapshots.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ppi.core.value_objects import (
    ContractError,
    EdgeKind,
    EdgeKindGroup,
    ModuleName,
    RelativeFilePath,
    SourceLine,
    edge_kind_group_of,
    edge_kind_of,
)

__all__ = [
    "EdgeFact",
    "EdgeKindCount",
    "EdgeBreakdown",
    "CouplingEdgeSnapshot",
    "reduce_edge_facts",
    "score_edge_snapshot",
    "edge_breakdown_of",
    "edge_facts_by_pair",
]


@dataclass(frozen=True, slots=True)
class EdgeFact:
    """One immutable piece of coupling evidence between two modules.

    ``source_quote`` is optional and provided by the adapter enricher, never
    read lazily by the fact itself.
    """

    source_module: ModuleName
    target_module: ModuleName
    kind: EdgeKind
    file_path: RelativeFilePath
    line: SourceLine | None
    detail: str
    source_quote: str = ""

    @property
    def pair(self) -> tuple[ModuleName, ModuleName]:
        """Return the (source, target) module pair key."""
        return (self.source_module, self.target_module)


@dataclass(frozen=True, slots=True)
class EdgeKindCount:
    """One (kind, count) record inside a coupling edge snapshot."""

    kind: EdgeKind
    count: int

    def __post_init__(self) -> None:
        # ponytail: __post_init__ — no factory, deal.inv does not fire on init.
        if not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 0:
            raise ContractError(
                f"EdgeKindCount.count must be a non-negative int, got {self.count!r}"
            )


@dataclass(frozen=True, slots=True)
class EdgeBreakdown:
    """Per-group graph-point breakdown for one coupling edge."""

    model_reuse: int = 0
    extension_or_method: int = 0
    view: int = 0
    field_property: int = 0

    @property
    def total(self) -> int:
        """Return the sum of all group points."""
        return self.model_reuse + self.extension_or_method + self.view + self.field_property

    @classmethod
    def from_kind_counts(cls, counts: Iterable[EdgeKindCount]) -> EdgeBreakdown:
        """Build a breakdown from typed kind counts via group dispatch."""
        model_reuse = 0
        extension_or_method = 0
        view = 0
        field_property = 0
        for record in counts:
            group = edge_kind_group_of(record.kind)
            match group:
                case EdgeKindGroup.MODEL_REUSE:
                    model_reuse += record.count
                case EdgeKindGroup.EXTENSION_OR_METHOD:
                    extension_or_method += record.count
                case EdgeKindGroup.VIEW:
                    view += record.count
                case EdgeKindGroup.FIELD_PROPERTY:
                    field_property += record.count
        return cls(
            model_reuse=model_reuse,
            extension_or_method=extension_or_method,
            view=view,
            field_property=field_property,
        )


@dataclass(frozen=True, slots=True)
class CouplingEdgeSnapshot:
    """Immutable snapshot of one directed coupling edge between two modules."""

    source_module: ModuleName
    target_module: ModuleName
    kind_counts: tuple[EdgeKindCount, ...] = ()
    evidence: tuple[EdgeFact, ...] = ()
    breakdown: EdgeBreakdown = field(default_factory=EdgeBreakdown)

    @property
    def score(self) -> int:
        """Return the total graph points for this edge."""
        return self.breakdown.total

    @property
    def kinds_map(self) -> Mapping[str, int]:
        """Return a read-only ``{kind_value: count}`` mapping (serialization boundary, F3)."""
        return MappingProxyType(
            {record.kind.value: record.count for record in self.kind_counts}
        )

    @property
    def has_evidence(self) -> bool:
        """Return True if the edge has any evidence facts."""
        return bool(self.evidence)


def edge_facts_by_pair(
    facts: Iterable[EdgeFact],
) -> Mapping[tuple[ModuleName, ModuleName], tuple[EdgeFact, ...]]:
    """Group an iterable of edge facts by their (source, target) pair."""
    grouped: dict[tuple[ModuleName, ModuleName], list[EdgeFact]] = {}
    for fact in facts:
        grouped.setdefault(fact.pair, []).append(fact)
    return {pair: tuple(items) for pair, items in grouped.items()}


def edge_breakdown_of(facts: Iterable[EdgeFact]) -> EdgeBreakdown:
    """Compute a typed breakdown from raw facts via group dispatch."""
    counter: Counter[EdgeKind] = Counter()
    for fact in facts:
        counter[fact.kind] += 1
    counts = tuple(EdgeKindCount(kind=kind, count=count) for kind, count in counter.items())
    return EdgeBreakdown.from_kind_counts(counts)


def score_edge_snapshot(snapshot: CouplingEdgeSnapshot) -> int:
    """Return the total score for a snapshot (delegates to breakdown.total)."""
    return snapshot.breakdown.total


def reduce_edge_facts(facts: Iterable[EdgeFact]) -> tuple[CouplingEdgeSnapshot, ...]:
    """Reduce a stream of :class:`EdgeFact` into immutable snapshots.

    Order of input does not affect the resulting graph state: facts are grouped
    by pair, kinds are counted deterministically, and breakdowns are derived via
    typed group dispatch. No I/O and no hidden mutation.
    """
    grouped = edge_facts_by_pair(facts)
    snapshots: list[CouplingEdgeSnapshot] = []
    for (source, target), pair_facts in grouped.items():
        counter: Counter[EdgeKind] = Counter()
        for fact in pair_facts:
            counter[fact.kind] += 1
        kind_counts = tuple(
            EdgeKindCount(kind=kind, count=count)
            for kind, count in sorted(counter.items(), key=lambda item: item[0].value)
        )
        breakdown = EdgeBreakdown.from_kind_counts(kind_counts)
        snapshots.append(
            CouplingEdgeSnapshot(
                source_module=source,
                target_module=target,
                kind_counts=kind_counts,
                evidence=pair_facts,
                breakdown=breakdown,
            )
        )
    snapshots.sort(key=lambda s: (s.source_module.value, s.target_module.value))
    return tuple(snapshots)


def edge_fact_from_strings(
    source_module: str,
    target_module: str,
    kind: str,
    file_path: str,
    line: int,
    detail: str,
    source_quote: str = "",
) -> EdgeFact | None:
    """Build an :class:`EdgeFact` from raw strings, dropping invalid ones.

    Boundary helper used where callers still produce stringly data; invalid
    module names / kinds / paths yield ``None`` so the caller can skip without
    raising. Strict domain code builds :class:`EdgeFact` directly from typed
    value objects.
    """
    src = ModuleName.parse(source_module)
    tgt = ModuleName.parse(target_module)
    kind_v = edge_kind_of(kind)
    if src is None or tgt is None or kind_v is None:
        return None
    try:
        rel = RelativeFilePath.of(file_path)
    except ValueError:
        return None
    return EdgeFact(
        source_module=src,
        target_module=tgt,
        kind=kind_v,
        file_path=rel,
        line=SourceLine.or_none(line),
        detail=detail,
        source_quote=source_quote,
    )
