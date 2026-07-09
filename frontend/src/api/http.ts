/**
 * openapi-fetch client factory.
 *
 * `publicHttp` is the typed runtime client for `publicApi.ts` and
 * `internalHttp` is the typed runtime client for the legacy
 * `internalApi.ts`. Both are backed by the same generated
 * `paths`/`components` types from `frontend/src/api/generated/schema.d.ts`.
 *
 * Re-run `make api-types` whenever the OpenAPI contract changes; the
 * generated types are checked into source control.
 */
import createClient from "openapi-fetch";

import type { paths } from "./generated/schema";

const baseUrl =
  (typeof import.meta !== "undefined" &&
    (import.meta as { env?: Record<string, string> }).env?.["VITE_API_BASE_URL"]) ||
  "";

const client = createClient<paths>({ baseUrl });

export const publicHttp = client;
export const internalHttp = client;

/**
 * Response shape returned by every openapi-fetch call. The library
 * returns either a success or error branch; the loose types here let
 * the public facade branch on `error` without fighting the strict
 * discriminated union that confuses `tsc --strict`.
 */
export type ApiResult<T> = {
  data: T | undefined;
  error: unknown;
  response: { status: number };
};
