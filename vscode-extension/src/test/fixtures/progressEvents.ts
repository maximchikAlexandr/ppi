/**
 * VS Code bridge fixture for progress events and bridge failures.
 *
 * Provides representative progress event samples for the progress
 * decode pipeline and typed failure scenarios.
 */

/** A progress event emitted by the CLI */
export interface ProgressEvent {
  readonly stage: string;
  readonly status: "started" | "running" | "completed" | "failed";
  readonly message: string;
  readonly progress?: number;
  readonly total?: number;
  readonly error?: string;
}

/** Valid progress event: started */
export const progressStarted: ProgressEvent = {
  stage: "odoo_project_analysis_pipeline",
  status: "started",
  message: "Starting analysis",
  progress: 0,
  total: 10,
};

/** Valid progress event: running */
export const progressRunning: ProgressEvent = {
  stage: "module_enrichment_pipeline",
  status: "running",
  message: "Enriching modules with code analysis",
  progress: 3,
  total: 10,
};

/** Valid progress event: completed */
export const progressCompleted: ProgressEvent = {
  stage: "odoo_project_analysis_pipeline",
  status: "completed",
  message: "Analysis complete",
  progress: 10,
  total: 10,
};

/** Valid progress event: failed */
export const progressFailed: ProgressEvent = {
  stage: "addons_path_validation",
  status: "failed",
  message: "Invalid addons paths",
  error: "No such directory: /invalid/path",
};

/** Malformed progress event (missing required fields) */
export const malformedProgress: Record<string, unknown> = {
  stage: "unknown",
  // Missing status field
  message: "Corrupted event",
};

/** Invalid JSON line (cannot be parsed) */
export const invalidJsonLine = "this is not json";

/** CLI spawn failure scenario */
export const spawnFailure: Error = new Error("Command not found: ppi");

/** RPC startup failure scenario */
export const rpcStartupFailure: Error = new Error(
  "Failed to start RPC datasource: port in use",
);

/** Cancellation token scenario */
export const cancellationOutcome = {
  _tag: "cancelled" as const,
  stage: "commit_iteration_pipeline",
  reason: "User cancelled analysis",
};
