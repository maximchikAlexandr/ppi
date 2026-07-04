/**
 * Frontend API/RPC read pipeline.
 *
 * Composes: request builder -> transport Effect adapter -> schema decode
 * -> DTO-to-domain mapping -> UI-safe error mapping.
 *
 * Each stage returns Effect with distinguishable typed errors so
 * transport, schema, and domain failures reach UI cleanly.
 */

import { Effect } from "effect";

import type { PipelineError } from "../rop/types";
import { pipelineError } from "../rop/effect";

import type { RpcResponse, AnalysisSnapshot } from "./__fixtures__/analysisResponses";

/**
 * Build an RPC request object.
 */
export function buildRequest(method: string, params: Record<string, unknown>, id = 1): string {
  return JSON.stringify({
    jsonrpc: "2.0",
    method,
    params,
    id,
  });
}

/**
 * Transport Effect adapter: execute an RPC call.
 */
export function executeTransport(
  url: string,
  body: string,
): Effect.Effect<string, PipelineError> {
  return Effect.tryPromise({
    try: async () => {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.text();
    },
    catch: (error) =>
      pipelineError(
        "transport",
        "executeTransport",
        String(error),
        error instanceof Error ? error : undefined,
      ),
  });
}

/**
 * Schema decode stage: parse JSON RPC response.
 */
export function decodeResponse(
  raw: string,
): Effect.Effect<RpcResponse<AnalysisSnapshot>, PipelineError> {
  return Effect.try({
    try: () => JSON.parse(raw) as RpcResponse<AnalysisSnapshot>,
    catch: (error) =>
      pipelineError(
        "schema",
        "decodeResponse",
        `Failed to parse RPC response: ${String(error)}`,
        error instanceof Error ? error : undefined,
      ),
  });
}

/**
 * DTO-to-domain mapping stage.
 */
export function mapDtoToDomain(
  response: RpcResponse<AnalysisSnapshot>,
): Effect.Effect<AnalysisSnapshot, PipelineError> {
  if (response.error) {
    return Effect.fail(
      pipelineError(
        "schema",
        "mapDtoToDomain",
        `RPC error [${response.error.code}]: ${response.error.message}`,
      ),
    );
  }
  if (!response.result) {
    return Effect.fail(
      pipelineError(
        "mapping",
        "mapDtoToDomain",
        "RPC response missing result",
      ),
    );
  }
  return Effect.succeed(response.result);
}

/**
 * UI-safe read error mapping stage.
 */
export function mapReadErrorForUi<E extends PipelineError>(error: E): PipelineError {
  return pipelineError(
    error.category,
    "mapReadErrorForUi",
    error.message,
    error.cause,
  );
}
