/**
 * Legacy /api/<method> RPC client.
 *
 * All generic frontend code must use ``publicApi.ts`` (typed openapi-fetch
 * facade) instead. This module is kept only for the legacy graph explorer
 * path (SnapshotPage) until the generic EntityGraph migration is complete;
 * it is a hard boundary — see ``scripts/check_frontend_boundaries.py``.
 */

import { z } from "zod";

import { getDataSource, type DataSource } from "./dataSource";

import {
  CommitRowSchema,
  GraphEdgeSchema,
  GraphNodeSchema,
  GraphResponseSchema,
  HotspotItemSchema,
  HotspotsResponseSchema,
  TimeseriesPointSchema,
  TimeseriesResponseSchema,
  UiConfigResponseSchema,
  UiMetricOptionSchema,
  UiOptionSchema,
  GenericTableRowSchema,
  GenericTableResponseSchema,
  RelationsResponseSchema,
} from "./legacySchemas";

export type CommitRow = z.infer<typeof CommitRowSchema>;
export type GraphEdge = z.infer<typeof GraphEdgeSchema>;
export type GraphNode = z.infer<typeof GraphNodeSchema>;
export type GraphResponse = z.infer<typeof GraphResponseSchema>;
export type HotspotItem = z.infer<typeof HotspotItemSchema>;
export type HotspotsResponse = z.infer<typeof HotspotsResponseSchema>;
export type TimeseriesPoint = z.infer<typeof TimeseriesPointSchema>;
export type TimeseriesResponse = z.infer<typeof TimeseriesResponseSchema>;
export type UiConfigResponse = z.infer<typeof UiConfigResponseSchema>;
export type UiMetricOption = z.infer<typeof UiMetricOptionSchema>;
export type UiOption = z.infer<typeof UiOptionSchema>;
export type GenericTableRow = z.infer<typeof GenericTableRowSchema>;
export type GenericTableResponse = z.infer<typeof GenericTableResponseSchema>;
export type RelationsResponse = z.infer<typeof RelationsResponseSchema>;

// ── Fetch wrappers ──────────────────────────────────────────────

function ds(): DataSource {
  return getDataSource();
}

export function fetchCommits(): Promise<CommitRow[]> {
  return ds().get<CommitRow[]>("commits");
}

export function fetchGraph(
  commitHash: string,
  includeZeroScore = false,
): Promise<GraphResponse> {
  return ds().get<GraphResponse>("graph", {
    commit: commitHash,
    include_zero_score: String(includeZeroScore),
  });
}

export function fetchSnapshotTableFiles(
  commitHash?: string,
  moduleName?: string,
): Promise<GenericTableResponse> {
  return ds().get<GenericTableResponse>("snapshot/table/files", {
    ...(commitHash ? { commit: commitHash } : {}),
    ...(moduleName ? { module: moduleName } : {}),
  });
}

export function fetchSnapshotTableModules(
  commitHash?: string,
): Promise<GenericTableResponse> {
  return ds().get<GenericTableResponse>("snapshot/table/modules", {
    ...(commitHash ? { commit: commitHash } : {}),
  });
}

export function fetchSnapshotRelations(
  commitHash: string,
): Promise<RelationsResponse> {
  return ds().get<RelationsResponse>("snapshot/relations", {
    commit: commitHash,
  });
}

export function fetchHotspots(params: {
  level: string;
  metric_id: string;
  by: "value" | "growth";
  limit?: number;
  agg?: string;
}): Promise<HotspotsResponse> {
  return ds().get<HotspotsResponse>("hotspots", params as Record<string, unknown>);
}

export function fetchTimeseries(params: {
  level: string;
  metric_id: string;
  name: string;
  agg?: string;
}): Promise<TimeseriesResponse> {
  return ds().get<TimeseriesResponse>("metrics/timeseries", params as Record<string, unknown>);
}

export function fetchUiConfig(): Promise<UiConfigResponse> {
  return ds().get<UiConfigResponse>("ui/config");
}
