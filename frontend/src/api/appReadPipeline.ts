/**
 * Frontend app read pipeline — higher-level composition.
 *
 * Composes the full read railway: URL setup -> request build -> transport
 * -> decode -> domain map -> typed error. Components call this one pipeline
 * instead of stitching stages themselves.
 */

import { Effect, pipe } from "effect";

import type { PipelineError } from "../rop/types";

import {
  buildRequest,
  executeTransport,
  decodeResponse,
  mapDtoToDomain,
  mapReadErrorForUi,
} from "./readPipeline";

import type { AnalysisSnapshot } from "./__fixtures__/analysisResponses";

export interface ReadContext {
  readonly rpcUrl: string;
  readonly method: string;
  readonly params: Record<string, unknown>;
}

export function appReadPipeline(
  context: ReadContext,
): Effect.Effect<AnalysisSnapshot, PipelineError> {
  return pipe(
    buildRequest(context.method, context.params),
    (body) => executeTransport(context.rpcUrl, body),
    Effect.flatMap(decodeResponse),
    Effect.flatMap(mapDtoToDomain),
    Effect.mapError(mapReadErrorForUi),
  );
}
