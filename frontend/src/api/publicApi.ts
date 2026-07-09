/**
 * Public /api/v1 facade for the generic frontend.
 *
 * This module is the ONLY public API facade for generic frontend code.
 * It must be imported by all generic pages and components. Never import
 * `frontend/src/api/generated/**` directly in generic code; never
 * import `frontend/src/legacy/**` from generic code.
 *
 * The typed runtime client (`publicHttp`, an `openapi-fetch` instance
 * bound to the generated `paths`) is the single source of transport
 * truth. Public domain types are produced by the adapters in
 * `frontend/src/api/adapters/**`.
 */

import { publicHttp, type ApiResult } from "./http";
import { adaptUiConfig } from "./adapters/uiConfigAdapter";
import { adaptEntities } from "./adapters/entityAdapter";
import { adaptGraph } from "./adapters/graphAdapter";
import { adaptTable } from "./adapters/tableAdapter";
import { adaptMetricTimeseries, adaptMetricHotspots } from "./adapters/dashboardAdapter";
import { adaptError } from "./adapters/errorAdapter";

import type { UiConfig } from "../registry/uiConfigTypes";
import type { EntityTarget } from "../domain/entity";
import type { EntityGraphModel } from "../domain/graph";
import type { TableProjection } from "../domain/table";
import type { MetricQueryResult } from "../domain/query";

export type StatusV1 = {
  projectId: string | null;
  branch: string | null;
  storePresent: boolean;
  writerActive: boolean;
  commitCount: number;
  apiStatus: string;
};

export type CommitSummaryV1 = {
  commitId: string;
  commitOrder: number;
  authoredAt: string | null;
  summary: string | null;
};

export type TableSummaryV1 = {
  id: string;
  label: string;
  entityKindId?: string | null;
  supportedActions?: string[];
};

function unwrap<T>(res: ApiResult<T>): T {
  if (res.error || !res.data) {
    throw adaptError(res.response.status, res.error);
  }
  return res.data as T;
}

export async function getStatusV1(): Promise<StatusV1> {
  return unwrap<StatusV1>(
    (await publicHttp.GET("/api/v1/status")) as ApiResult<StatusV1>,
  );
}

export async function getUiConfigV1(): Promise<UiConfig> {
  return adaptUiConfig(
    unwrap<never>((await publicHttp.GET("/api/v1/ui/config")) as ApiResult<never>),
  );
}

export async function listCommitsV1(): Promise<CommitSummaryV1[]> {
  const body = unwrap<{ items?: CommitSummaryV1[] }>(
    (await publicHttp.GET("/api/v1/commits")) as ApiResult<{
      items?: CommitSummaryV1[];
    }>,
  );
  return body.items ?? [];
}

export async function listEntitiesV1(params: {
  entityKindId: string;
  commitId?: string | null;
  limit?: number;
}): Promise<EntityTarget[]> {
  return adaptEntities(
    unwrap<never>(
      (await publicHttp.GET("/api/v1/entities", {
        params: {
          query: {
            entityKindId: params.entityKindId,
            commitId: params.commitId ?? null,
            limit: params.limit,
          },
        },
      })) as ApiResult<never>,
    ),
  );
}

export async function getGraphV1(params: {
  lensId: string;
  commitId?: string | null;
  includeZeroWeight?: boolean;
}): Promise<EntityGraphModel> {
  return adaptGraph(
    unwrap<never>(
      (await publicHttp.GET("/api/v1/graph", {
        params: {
          query: {
            lensId: params.lensId,
            commitId: params.commitId ?? null,
            includeZeroWeight: params.includeZeroWeight ?? false,
          },
        },
      })) as ApiResult<never>,
    ),
  );
}

export async function listTablesV1(): Promise<TableSummaryV1[]> {
  const body = unwrap<{ items?: TableSummaryV1[] }>(
    (await publicHttp.GET("/api/v1/tables")) as ApiResult<{
      items?: TableSummaryV1[];
    }>,
  );
  return body.items ?? [];
}

export async function getTableV1(params: {
  tableId: string;
  commitId?: string | null;
  parentEntityId?: string | null;
  limit?: number;
}): Promise<TableProjection> {
  return adaptTable(
    unwrap<never>(
      (await publicHttp.GET("/api/v1/tables/{tableId}", {
        params: {
          path: { tableId: params.tableId },
          query: {
            commitId: params.commitId ?? null,
            parentEntityId: params.parentEntityId ?? null,
            limit: params.limit,
          },
        },
      })) as ApiResult<never>,
    ),
  );
}

export async function getMetricTimeseriesV1(params: {
  entityKindId: string;
  metricId: string;
  aggregation: string;
  targetId?: string | null;
  commitId?: string | null;
}): Promise<MetricQueryResult> {
  return adaptMetricTimeseries(
    unwrap<never>(
      (await publicHttp.GET("/api/v1/metrics/timeseries", {
        params: {
          query: {
            entityKindId: params.entityKindId,
            metricId: params.metricId,
            aggregation: params.aggregation,
            targetId: params.targetId ?? null,
            commitId: params.commitId ?? null,
          },
        },
      })) as ApiResult<never>,
    ),
  );
}

export async function getMetricHotspotsV1(params: {
  entityKindId: string;
  metricId: string;
  aggregation: string;
  rankBy: "value" | "growth";
  limit?: number;
}): Promise<MetricQueryResult> {
  return adaptMetricHotspots(
    unwrap<never>(
      (await publicHttp.GET("/api/v1/metrics/hotspots", {
        params: {
          query: {
            entityKindId: params.entityKindId,
            metricId: params.metricId,
            aggregation: params.aggregation,
            rankBy: params.rankBy,
            limit: params.limit,
          },
        },
      })) as ApiResult<never>,
    ),
  );
}