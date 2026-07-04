/**
 * Effect adapter helpers for transport, decode, and domain mapping.
 *
 * These utilities wrap Effect-based error handling into the PPI
 * PipelineError convention so all frontend read pipeline stages
 * speak a consistent typed-error vocabulary.
 */

import type { PipelineError, PipelineErrorCategory } from "./types";

/**
 * Build a typed PipelineError from category + details.
 */
export function pipelineError(
  category: PipelineErrorCategory,
  stage: string,
  message: string,
  cause?: unknown,
): PipelineError {
  return {
    category,
    stage,
    message,
    safeInputId: "",
    cause,
  };
}
