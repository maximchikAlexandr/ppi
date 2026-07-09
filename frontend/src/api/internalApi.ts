/**
 * Internal API facade. Used only by legacy adapters and diagnostics.
 * Generic frontend code MUST NOT import this module directly.
 *
 * Uses the same typed `openapi-fetch` client as `publicApi.ts` so
 * legacy code paths share the generated `paths` types.
 */

import { internalHttp, type ApiResult } from "./http";

function unwrap<T>(res: ApiResult<T>): T {
  if (res.error || !res.data) {
    throw new Error(`legacy request failed: ${res.response.status}`);
  }
  return res.data as T;
}

export async function getLegacyGraph(commit: string) {
  return unwrap<unknown>(
    (await internalHttp.GET("/api/graph", {
      params: { query: { commit, include_zero_score: false } },
    })) as ApiResult<unknown>,
  );
}

export async function getLegacySnapshotTableModules(commit?: string) {
  return unwrap<unknown>(
    (await internalHttp.GET("/api/snapshot/table/modules", {
      params: { query: { commit: commit ?? "" } },
    })) as ApiResult<unknown>,
  );
}

export async function getLegacySnapshotTableFiles(
  commit?: string,
  moduleName?: string,
) {
  return unwrap<unknown>(
    (await internalHttp.GET("/api/snapshot/table/files", {
      params: { query: { commit: commit ?? "", module: moduleName ?? "" } },
    })) as ApiResult<unknown>,
  );
}
