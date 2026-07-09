/**
 * Adapter: /api/v1/metrics/{timeseries,hotspots} DTO -> dashboard domain
 * results.
 */
import type {
  MetricHotspotsResult,
  MetricQueryResult,
  MetricTimeseriesResult,
} from "../../domain/query";

type TimeseriesDto = {
  entityKindId?: string;
  metricId?: string;
  aggregation?: string;
  targetId?: string | null;
  series?: {
    label?: string;
    points?: { commitOrder?: number; commitId?: string; value?: number | null }[];
  }[];
};

type HotspotsDto = {
  entityKindId?: string;
  metricId?: string;
  aggregation?: string;
  rankBy?: string;
  items?: {
    entity?: { id?: string; kind?: string; label?: string };
    current?: number;
    first?: number | null;
    growth?: number | null;
  }[];
};

export function adaptMetricTimeseries(dto: TimeseriesDto): MetricQueryResult {
  const result: MetricTimeseriesResult = {
    entityKindId: (dto.entityKindId ?? "") as MetricTimeseriesResult["entityKindId"],
    metricId: (dto.metricId ?? "") as MetricTimeseriesResult["metricId"],
    aggregation: dto.aggregation ?? "",
    series: (dto.series ?? []).map((s) => ({
      label: s.label ?? "",
      points: (s.points ?? []).map((p) => ({
        commitOrder: p.commitOrder ?? 0,
        commitId: p.commitId ?? "",
        value: p.value ?? null,
      })),
    })),
  };
  return { queryId: "metrics.timeseries", resultKind: "timeseries", result };
}

export function adaptMetricHotspots(dto: HotspotsDto): MetricQueryResult {
  const result: MetricHotspotsResult = {
    entityKindId: (dto.entityKindId ?? "") as MetricHotspotsResult["entityKindId"],
    metricId: (dto.metricId ?? "") as MetricHotspotsResult["metricId"],
    aggregation: dto.aggregation ?? "",
    rankBy: dto.rankBy ?? "value",
    items: (dto.items ?? []).map((it) => ({
      entity: {
        id: it.entity?.id ?? "",
        kind: it.entity?.kind ?? "",
        label: it.entity?.label ?? "",
      },
      current: it.current ?? 0,
      first: it.first ?? null,
      growth: it.growth ?? null,
    })),
  };
  return { queryId: "metrics.hotspots", resultKind: "ranking", result };
}