/**
 * Progress event stream decoder.
 *
 * Parses JSON progress events from the CLI stdout and decodes them
 * into typed progress states. Malformed events are returned as typed
 * BridgeFailures.
 */

import { Effect } from "effect";

import type { BridgeFailure } from "../rop/types";
import { bridgeFailure } from "../rop/types";

/** Parsed progress event */
export interface ProgressEvent {
  readonly stage: string;
  readonly status: "started" | "running" | "completed" | "failed";
  readonly message: string;
  readonly progress?: number;
  readonly total?: number;
  readonly error?: string;
}

/**
 * Decode a single progress event line into a typed ProgressEvent.
 */
export function decodeProgressEvent(
  line: string,
): Effect.Effect<ProgressEvent, BridgeFailure> {
  return Effect.try({
    try: () => {
      const parsed = JSON.parse(line);

      if (
        typeof parsed.stage !== "string" ||
        typeof parsed.status !== "string"
      ) {
        throw new Error("Missing required fields: stage, status");
      }

      return {
        stage: parsed.stage,
        status: parsed.status as ProgressEvent["status"],
        message: parsed.message ?? "",
        progress: parsed.progress,
        total: parsed.total,
        error: parsed.error,
      };
    },
    catch: (error) =>
      bridgeFailure(
        "progress",
        "decodeProgressEvent",
        `Malformed progress event: ${String(error)}`,
        error instanceof Error ? error : undefined,
      ),
  });
}
