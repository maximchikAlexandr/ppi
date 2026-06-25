"""Unit tests for immutable edge facts and the pure edge reducer."""

from __future__ import annotations

import pytest

from ppi.core.odoo.facts import (
    CouplingEdgeSnapshot,
    EdgeBreakdown,
    EdgeFact,
    EdgeKindCount,
    edge_breakdown_of,
    edge_fact_from_strings,
    edge_facts_by_pair,
    reduce_edge_facts,
)
from ppi.core.value_objects import (
    EdgeKind,
    EdgeKindGroup,
    ModuleName,
    RelativeFilePath,
    SourceLine,
    edge_kind_group_of,
)


def _fact(source: str, target: str, kind: EdgeKind, line: int = 1, detail: str = "d") -> EdgeFact:
    return EdgeFact(
        source_module=ModuleName.of(source),
        target_module=ModuleName.of(target),
        kind=kind,
        file_path=RelativeFilePath.of("models/x.py"),
        line=SourceLine.or_none(line),
        detail=detail,
    )


def test_edge_fact_pair():
    f = _fact("sale", "base", EdgeKind.PYTHON_MANY2ONE)
    assert f.pair == (ModuleName.of("sale"), ModuleName.of("base"))


def test_edge_kind_count_rejects_negative():
    with pytest.raises(ValueError):
        EdgeKindCount(kind=EdgeKind.XML_REF, count=-1)


def test_edge_breakdown_from_kind_counts_dispatch():
    counts = (
        EdgeKindCount(EdgeKind.PYTHON_MANY2ONE, 2),
        EdgeKindCount(EdgeKind.XML_REF, 3),
        EdgeKindCount(EdgeKind.PYTHON_FIELD_PROPERTY_ACCESS, 1),
        EdgeKindCount(EdgeKind.PYTHON_METHOD_CALL, 4),
    )
    bd = EdgeBreakdown.from_kind_counts(counts)
    assert bd.model_reuse == 2
    assert bd.view == 3
    assert bd.field_property == 1
    assert bd.extension_or_method == 4
    assert bd.total == 10


def test_edge_breakdown_empty():
    assert EdgeBreakdown.from_kind_counts(()).total == 0
    assert EdgeBreakdown().total == 0


def test_reduce_edge_facts_groups_by_pair():
    facts = (
        _fact("sale", "base", EdgeKind.PYTHON_MANY2ONE, 10),
        _fact("sale", "base", EdgeKind.PYTHON_MANY2ONE, 12),
        _fact("sale", "base", EdgeKind.XML_REF, 5),
        _fact("base", "sale", EdgeKind.PYTHON_INHERIT, 3),
    )
    snapshots = reduce_edge_facts(facts)
    assert len(snapshots) == 2
    ab = snapshots[1]
    assert ab.source_module == ModuleName.of("sale")
    assert ab.target_module == ModuleName.of("base")
    assert ab.kinds_map == {"python_many2one": 2, "xml_ref": 1}
    assert ab.breakdown.model_reuse == 2
    assert ab.breakdown.view == 1
    assert ab.score == 3
    assert len(ab.evidence) == 3


def test_reduce_edge_facts_order_independent():
    facts_a = (
        _fact("sale", "base", EdgeKind.PYTHON_MANY2ONE, 1),
        _fact("sale", "base", EdgeKind.XML_REF, 2),
    )
    facts_b = reversed(facts_a)
    sa = reduce_edge_facts(facts_a)
    sb = reduce_edge_facts(facts_b)
    assert sa[0].kinds_map == sb[0].kinds_map
    assert sa[0].score == sb[0].score


def test_reduce_edge_facts_empty():
    assert reduce_edge_facts(()) == ()


def test_edge_facts_by_pair():
    facts = (
        _fact("sale", "base", EdgeKind.PYTHON_MANY2ONE),
        _fact("sale", "base", EdgeKind.XML_REF),
        _fact("base", "sale", EdgeKind.PYTHON_INHERIT),
    )
    grouped = edge_facts_by_pair(facts)
    assert len(grouped) == 2
    assert len(grouped[ModuleName.of("sale"), ModuleName.of("base")]) == 2


def test_edge_breakdown_of_facts():
    facts = (
        _fact("a", "b", EdgeKind.PYTHON_MANY2ONE),
        _fact("a", "b", EdgeKind.XML_REF),
        _fact("a", "b", EdgeKind.XML_REF),
    )
    bd = edge_breakdown_of(facts)
    assert bd.model_reuse == 1
    assert bd.view == 2
    assert bd.total == 3


def test_edge_fact_from_strings_valid():
    f = edge_fact_from_strings("sale", "base", "python__inherit", "f.py", 5, "d", "q")
    assert f is not None
    assert f.kind is EdgeKind.PYTHON_INHERIT
    assert f.line is not None and int(f.line) == 5
    assert f.source_quote == "q"


def test_edge_fact_from_strings_invalid_returns_none():
    assert edge_fact_from_strings("bad name", "base", "python__inherit", "f.py", 5, "d") is None
    assert edge_fact_from_strings("sale", "base", "nope", "f.py", 5, "d") is None
    assert edge_fact_from_strings("sale", "base", "python__inherit", "/abs", 5, "d") is None


def test_edge_fact_from_strings_line_zero_becomes_none():
    f = edge_fact_from_strings("sale", "base", "python__inherit", "f.py", 0, "d")
    assert f is not None and f.line is None


def test_coupling_edge_snapshot_kinds_map():
    snap = CouplingEdgeSnapshot(
        source_module=ModuleName.of("sale"),
        target_module=ModuleName.of("base"),
        kind_counts=(EdgeKindCount(EdgeKind.XML_REF, 2),),
    )
    assert snap.kinds_map == {"xml_ref": 2}


def test_edge_kind_group_of_all_kinds():
    for kind in EdgeKind:
        assert edge_kind_group_of(kind) in EdgeKindGroup