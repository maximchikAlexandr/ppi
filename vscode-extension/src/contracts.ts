/**
 * Shared event/error contracts for the PPI VS Code bridge.
 *
 * Progress event types are generated from ``src/ppi/runtime/progress.py`` via
 * ``ppi dev generate-contracts``. Handwritten types (CliNotFound) and
 * runtime constants (TERMINAL_EVENT_TYPES) remain here.
 */

export type { ProgressEvent, RunCompleted, RunFailed } from "./contracts/progressEvents";

/** Event types that terminate a run (used to resolve the `done` promise). */
export const TERMINAL_EVENT_TYPES = new Set(["run_completed", "run_failed"]);

/** Raised when the resolved `ppi` CLI executable cannot be launched (FR-014). */
export class CliNotFound extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CliNotFound";
  }
}
