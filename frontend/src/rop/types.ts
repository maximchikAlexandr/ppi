/**
 * TypeScript ROP pipeline stage types for the PPI frontend.
 *
 * Pure sync stages are typed functions returning the output directly or
 * an Either variant for fallible operations. Effectful stages use the
 * Effect type for async/resource/error tracking.
 */

/**
 * Categories of typed errors in the frontend read pipeline.
 */
export type PipelineErrorCategory =
  | "validation"
  | "transport"
  | "schema"
  | "mapping"
  | "domain";

/**
 * Typed error for the frontend read/view-model pipelines.
 */
export interface PipelineError {
  readonly category: PipelineErrorCategory;
  readonly stage: string;
  readonly message: string;
  readonly safeInputId: string;
  readonly cause?: unknown;
}
