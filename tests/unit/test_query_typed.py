"""Unit tests for typed query errors and request value objects."""

from __future__ import annotations

import pytest

from ppi.query.errors import QueryError, QueryErrorCode, QueryFailure, raise_query_failure
from ppi.query.requests import (
    Aggregation,
    CatalogLevel,
    CatalogQuery,
    EdgesQuery,
    HotspotBy,
    HotspotMetric,
    HotspotsQuery,
    SnapshotFileQuery,
    SnapshotModuleQuery,
    StructureTimeseriesQuery,
)

# --- errors ----------------------------------------------------------------


def test_query_failure_of_ok():
    f = QueryFailure.of("INVALID_PARAMS", "x required", http_status=422)
    assert f.code is QueryErrorCode.INVALID_PARAMS
    assert f.http_status == 422


def test_query_failure_rejects_empty_message():
    with pytest.raises(ValueError):
        QueryFailure.of("INVALID_PARAMS", "", http_status=422)


def test_query_failure_rejects_out_of_range_status():
    with pytest.raises(ValueError):
        QueryFailure.of("INVALID_PARAMS", "ok", http_status=200)
    with pytest.raises(ValueError):
        QueryFailure.of("INVALID_PARAMS", "ok", http_status=600)


def test_query_error_wrapper_legacy_props():
    try:
        raise_query_failure("METHOD_NOT_FOUND", "unknown", http_status=404)
    except QueryError as exc:
        assert exc.code == "METHOD_NOT_FOUND"
        assert exc.message == "unknown"
        assert exc.http_status == 404
        assert exc.failure.code is QueryErrorCode.METHOD_NOT_FOUND


def test_raise_query_failure_raises():
    with pytest.raises(QueryError):
        raise_query_failure("LOCKED", "busy", http_status=409)


# --- requests --------------------------------------------------------------


def test_catalog_query_from_params():
    q = CatalogQuery.from_params({"level": "file", "limit": "10"})
    assert q.level is CatalogLevel.FILE
    assert q.limit == 10


def test_catalog_query_default_limit():
    q = CatalogQuery.from_params({"level": "module"})
    assert q.limit == 5000


def test_hotspots_query_defaults():
    q = HotspotsQuery.from_params({})
    assert q.level is CatalogLevel.MODULE
    assert q.metric is HotspotMetric.CYCLOMATIC
    assert q.by is HotspotBy.VALUE
    assert q.limit == 20
    assert q.agg is Aggregation.MEAN


def test_hotspots_query_explicit():
    q = HotspotsQuery.from_params(
        {"level": "file", "metric": "cognitive", "by": "growth", "limit": "5", "agg": "max"}
    )
    assert q.level is CatalogLevel.FILE
    assert q.metric is HotspotMetric.COGNITIVE
    assert q.by is HotspotBy.GROWTH
    assert q.limit == 5
    assert q.agg is Aggregation.MAX


def test_edges_query_from_params():
    q = EdgesQuery.from_params({"commit": "abc", "min_score": "5"})
    assert q.commit == "abc"
    assert q.min_score == 5
    assert q.effective_threshold == 5


def test_edges_query_effective_threshold_zero():
    q = EdgesQuery.from_params({"min_score": 0})
    assert q.effective_threshold == 1


def test_edges_query_effective_threshold_zero_with_include():
    q = EdgesQuery.from_params({"min_score": 0, "include_zero_score": "true"})
    assert q.effective_threshold == 0


def test_structure_timeseries_query():
    q = StructureTimeseriesQuery.from_params({"include_zero_score": "true"})
    assert q.include_zero_score is True
    q2 = StructureTimeseriesQuery.from_params({})
    assert q2.include_zero_score is False


def test_snapshot_module_query():
    q = SnapshotModuleQuery.from_params({"module": "sale"})
    assert q.module == "sale"
    assert q.commit is None


def test_snapshot_module_query_requires_module():
    with pytest.raises(Exception) as exc_info:  # noqa: PT012
        SnapshotModuleQuery.from_params({})
    assert getattr(exc_info.value, "code", None) == "INVALID_PARAMS"


def test_snapshot_file_query():
    q = SnapshotFileQuery.from_params({"commit": "abc", "module": "sale"})
    assert q.commit == "abc"
    assert q.module == "sale"