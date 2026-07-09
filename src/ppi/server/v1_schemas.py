"""Public Pydantic v2 schemas for ``/api/v1`` endpoints.

Pydantic lives ONLY here (the FastAPI boundary): request/response
validation + OpenAPI schema generation for the frontend type pipeline.
The ``CamelModel`` alias generator is the SOLE camelCase authority —
projections.py returns snake_case dicts and this layer serializes them.

ponytail: typed sub-models for UiConfig replace the earlier
``dict[str, Any]`` registry shapes; this is the single source of truth
for both backend validation and the generated TS types. Add a field to
a model below and it flows through OpenAPI -> openapi-typescript ->
frontend typed client with zero manual duplication.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
    """Base Pydantic model exposing fields in camelCase."""

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
        extra="ignore",
    )


class ErrorBody(CamelModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = Field(default=None)


class ErrorResponse(CamelModel):
    error: ErrorBody


class StatusV1Response(CamelModel):
    project_id: str | None = None
    branch: str | None = None
    store_present: bool
    writer_active: bool
    commit_count: int = 0
    api_status: str = "experimental"


class CommitSummaryV1(CamelModel):
    commit_id: str
    commit_order: int
    authored_at: str | None = None
    summary: str | None = None


class ListCommitsV1Response(CamelModel):
    items: list[CommitSummaryV1] = Field(default_factory=list)


class ProfileV1(CamelModel):
    id: str = "ppi.default"
    label: str = "Default"
    plugin_ids: list[str] = Field(default_factory=list)


class CapabilityV1(CamelModel):
    id: str
    label: str
    enabled: bool = False


class PageDefV1(CamelModel):
    id: str
    label: str
    kind: str
    required_capabilities: list[str] = Field(default_factory=list)
    default_visible: bool = True


class EntityKindDefV1(CamelModel):
    id: str
    label: str
    plugin_id: str | None = None


class MetricFormatV1(CamelModel):
    kind: str = "integer"


class MetricDefV1(CamelModel):
    id: str
    label: str
    value_type: str
    scope: str
    entity_kinds: list[str] = Field(default_factory=list)
    supported_aggregations: list[str] = Field(default_factory=list)
    default_aggregation: str = "mean"
    supported_views: list[str] = Field(default_factory=list)
    higher_is_worse: bool = False
    format: MetricFormatV1 = Field(default_factory=MetricFormatV1)


class RelationTypeV1(CamelModel):
    id: str
    label: str
    default_visible: bool = False
    group: str | None = None
    plugin_id: str | None = None


class LineCategoryV1(CamelModel):
    id: str
    label: str
    default_visible: bool = False
    order: int = 0


class VisualEncodingV1(CamelModel):
    id: str
    label: str | None = None
    kind: str = "nodeSize"


class GraphLensV1(CamelModel):
    id: str
    label: str
    node_kinds: list[str] = Field(default_factory=list)
    relation_types: list[str] = Field(default_factory=list)
    default_visual_encoding: dict[str, Any] = Field(default_factory=dict)


class TableDefV1(CamelModel):
    id: str
    label: str
    entity_kind_id: str | None = None
    supported_actions: list[str] = Field(default_factory=list)
    default_sort: dict[str, Any] | None = None


class QueryParameterDefV1(CamelModel):
    id: str
    label: str
    kind: str
    required: bool = False


class QueryDefV1(CamelModel):
    id: str
    label: str
    result_kind: str
    parameters: list[QueryParameterDefV1] = Field(default_factory=list)


class UiConfigV1Response(CamelModel):
    schema_version: int = 1
    profile: ProfileV1 = Field(default_factory=ProfileV1)
    plugins: list[dict[str, Any]] = Field(default_factory=list)
    capabilities: list[CapabilityV1] = Field(default_factory=list)
    pages: list[PageDefV1] = Field(default_factory=list)
    entity_kinds: list[EntityKindDefV1] = Field(default_factory=list)
    metrics: list[MetricDefV1] = Field(default_factory=list)
    relation_types: list[RelationTypeV1] = Field(default_factory=list)
    line_categories: list[LineCategoryV1] = Field(default_factory=list)
    visual_encodings: list[VisualEncodingV1] = Field(default_factory=list)
    graph_lenses: list[GraphLensV1] = Field(default_factory=list)
    tables: list[TableDefV1] = Field(default_factory=list)
    queries: list[QueryDefV1] = Field(default_factory=list)


class EntityRefV1(CamelModel):
    id: str
    kind: str
    label: str
    path: str | None = None
    plugin_id: str | None = None


class EntityTargetV1(EntityRefV1):
    selectable: bool = True
    reason: str | None = None


class ListEntitiesV1Response(CamelModel):
    entity_kind_id: str
    commit_id: str | None = None
    items: list[EntityTargetV1] = Field(default_factory=list)


class MetricValueV1(CamelModel):
    metric_id: str
    value: float | int | str | bool | None = None
    aggregation: str | None = None


class GraphNodeV1(CamelModel):
    entity: EntityRefV1
    metrics: list[MetricValueV1] = Field(default_factory=list)
    distributions: list[dict[str, Any]] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    line_counts: dict[str, int] = Field(default_factory=dict)


class GraphEdgeV1(CamelModel):
    id: str
    source: EntityRefV1
    target: EntityRefV1
    relation_type_id: str
    metrics: list[MetricValueV1] = Field(default_factory=list)
    contributions: list[dict[str, Any]] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class GraphV1Response(CamelModel):
    commit_id: str
    lens_id: str
    nodes: list[GraphNodeV1] = Field(default_factory=list)
    edges: list[GraphEdgeV1] = Field(default_factory=list)
    metrics: list[MetricDefV1] = Field(default_factory=list)
    relation_types: list[RelationTypeV1] = Field(default_factory=list)


class TableColumnV1(CamelModel):
    id: str
    label: str
    value_type: str = "string"
    metric_id: str | None = None
    format: dict[str, Any] | None = None
    sortable: bool = True
    visible_by_default: bool = True
    align: str | None = None
    width: int | None = None


class TableRowActionV1(CamelModel):
    id: str
    label: str
    kind: str = "drilldown"
    target_table_id: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class TableRowV1(CamelModel):
    id: str
    cells: dict[str, Any] = Field(default_factory=dict)
    actions: list[TableRowActionV1] = Field(default_factory=list)


class TableV1Response(CamelModel):
    table_id: str
    title: str
    commit_id: str | None = None
    columns: list[TableColumnV1] = Field(default_factory=list)
    rows: list[TableRowV1] = Field(default_factory=list)


class ListTablesV1Response(CamelModel):
    items: list[TableDefV1] = Field(default_factory=list)


class MetricTimeseriesPointV1(CamelModel):
    commit_order: int
    commit_id: str
    value: float | int | None = None


class MetricTimeseriesSeriesV1(CamelModel):
    label: str
    points: list[MetricTimeseriesPointV1] = Field(default_factory=list)


class MetricTimeseriesV1Response(CamelModel):
    entity_kind_id: str
    metric_id: str
    aggregation: str
    target_id: str | None = None
    series: list[MetricTimeseriesSeriesV1] = Field(default_factory=list)


class MetricHotspotsItemV1(CamelModel):
    entity: EntityRefV1
    current: float
    first: float | None = None
    growth: float | None = None


class MetricHotspotsV1Response(CamelModel):
    entity_kind_id: str
    metric_id: str
    aggregation: str
    rank_by: str = "value"
    items: list[MetricHotspotsItemV1] = Field(default_factory=list)