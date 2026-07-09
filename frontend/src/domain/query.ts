import type { EntityId, EntityKindId, MetricId } from "./ids";

export type QueryResultKind = "timeseries" | "ranking" | "distribution";

export type QueryParameterKind =
  | "entityKind"
  | "target"
  | "metric"
  | "aggregation"
  | "number"
  | "select";

export type QueryParameterDefinition = {
  id: string;
  label: string;
  kind: QueryParameterKind;
  required: boolean;
};

export type QueryDefinition = {
  id: string;
  label: string;
  resultKind: QueryResultKind;
  parameters: QueryParameterDefinition[];
};

export type MetricQueryState = {
  entityKindId: EntityKindId;
  targetId?: EntityId | null;
  metricId: MetricId;
  aggregation: string;
};

export type MetricQueryStateResult =
  | { status: "valid"; state: MetricQueryState }
  | { status: "unavailable"; reason: string };

export type TimeseriesPoint = {
  commitOrder: number;
  commitId: string;
  value: number | null;
};

export type TimeseriesSeries = {
  label: string;
  points: TimeseriesPoint[];
};

export type HotspotItem = {
  entity: { id: string; kind: string; label: string };
  current: number;
  first: number | null;
  growth: number | null;
};

export type MetricTimeseriesResult = {
  entityKindId: EntityKindId;
  metricId: MetricId;
  aggregation: string;
  series: TimeseriesSeries[];
};

export type MetricHotspotsResult = {
  entityKindId: EntityKindId;
  metricId: MetricId;
  aggregation: string;
  rankBy: string;
  items: HotspotItem[];
};

export type MetricQueryResult =
  | { queryId: "metrics.timeseries"; resultKind: "timeseries"; result: MetricTimeseriesResult }
  | { queryId: "metrics.hotspots"; resultKind: "ranking"; result: MetricHotspotsResult };
