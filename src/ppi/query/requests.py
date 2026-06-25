"""Typed request value objects for query endpoints (PPI-043).

Each request is an immutable value object built by a ``from_params`` factory
that performs coercion/validation of the raw ``params: Mapping[str, object]``
coming from HTTP/RPC. Recoverable user errors raise :class:`QueryError`
(wrapping a frozen :class:`QueryFailure`); programmer/contract violations are
fail-fast.

Handlers migrate to accepting these typed requests instead of raw ``dict``;
the legacy ``_opt_*`` helpers are reused inside the factories so behavior stays
identical.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from ppi.query._params import _choice, _opt_bool, _opt_int, _opt_str, _req

__all__ = [
    "CatalogLevel",
    "CatalogQuery",
    "Aggregation",
    "HotspotsQuery",
    "HotspotMetric",
    "HotspotBy",
    "EdgesQuery",
    "StructureTimeseriesQuery",
    "SnapshotModuleQuery",
    "SnapshotFileQuery",
]


class CatalogLevel(StrEnum):
    """Catalog granularity."""

    MODULE = "module"
    FILE = "file"


class Aggregation(StrEnum):
    """Aggregation kind for timeseries/hotspots."""

    MEAN = "mean"
    MEDIAN = "median"
    P95 = "p95"
    MAX = "max"


class HotspotMetric(StrEnum):
    """Supported hotspot metrics."""

    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    JONES = "jones"
    PYTHON_FILE_COUNT = "python_file_count"


class HotspotBy(StrEnum):
    """Hotspot ranking basis."""

    VALUE = "value"
    GROWTH = "growth"


@dataclass(frozen=True, slots=True)
class CatalogQuery:
    """Request for the ``catalog`` endpoint."""

    level: CatalogLevel
    limit: int

    @classmethod
    def from_params(cls, params: Mapping[str, object]) -> CatalogQuery:
        """Build a catalog request from raw params."""
        level = CatalogLevel(_choice(dict(params), "level", {"module", "file"}))
        limit = _opt_int(dict(params), "limit", 5000)
        return cls(level=level, limit=limit)


@dataclass(frozen=True, slots=True)
class HotspotsQuery:
    """Request for the ``hotspots`` endpoint."""

    level: CatalogLevel
    metric: HotspotMetric
    by: HotspotBy
    limit: int
    agg: Aggregation

    @classmethod
    def from_params(cls, params: Mapping[str, object]) -> HotspotsQuery:
        """Build a hotspots request from raw params."""
        level = CatalogLevel(_choice(dict(params), "level", {"module", "file"}, default="module"))
        metric = HotspotMetric(
            _choice(
                dict(params),
                "metric",
                {"cyclomatic", "cognitive", "jones", "python_file_count"},
                default="cyclomatic",
            )
        )
        by = HotspotBy(_choice(dict(params), "by", {"value", "growth"}, default="value"))
        limit = _opt_int(dict(params), "limit", 20)
        agg = Aggregation(
            _choice(dict(params), "agg", {"mean", "median", "p95", "max"}, default="mean")
        )
        return cls(level=level, metric=metric, by=by, limit=limit, agg=agg)


@dataclass(frozen=True, slots=True)
class EdgesQuery:
    """Request for the ``edges`` endpoint."""

    commit: str | None
    min_score: int
    include_zero_score: bool

    @classmethod
    def from_params(cls, params: Mapping[str, object]) -> EdgesQuery:
        """Build an edges request from raw params."""
        commit = _opt_str(dict(params), "commit")
        min_score = _opt_int(dict(params), "min_score", 0)
        include_zero_score = _opt_bool(dict(params), "include_zero_score", False)
        return cls(commit=commit, min_score=min_score, include_zero_score=include_zero_score)

    @property
    def effective_threshold(self) -> int:
        """Return the score threshold honoring ``include_zero_score``."""
        return self.min_score if self.include_zero_score else max(self.min_score, 1)


@dataclass(frozen=True, slots=True)
class StructureTimeseriesQuery:
    """Request for the ``structure/timeseries`` endpoint."""

    include_zero_score: bool

    @classmethod
    def from_params(cls, params: Mapping[str, object]) -> StructureTimeseriesQuery:
        """Build a structure-timeseries request from raw params."""
        return cls(include_zero_score=_opt_bool(dict(params), "include_zero_score", False))


@dataclass(frozen=True, slots=True)
class SnapshotModuleQuery:
    """Request for the ``snapshot/module`` endpoint."""

    module: str
    commit: str | None

    @classmethod
    def from_params(cls, params: Mapping[str, object]) -> SnapshotModuleQuery:
        """Build a snapshot-module request from raw params."""
        module = _req(dict(params), "module")
        commit = _opt_str(dict(params), "commit")
        return cls(module=module, commit=commit)


@dataclass(frozen=True, slots=True)
class SnapshotFileQuery:
    """Request for the ``snapshot/file`` endpoint."""

    commit: str | None
    module: str | None

    @classmethod
    def from_params(cls, params: Mapping[str, object]) -> SnapshotFileQuery:
        """Build a snapshot-file request from raw params."""
        commit = _opt_str(dict(params), "commit")
        module = _opt_str(dict(params), "module")
        return cls(commit=commit, module=module)
