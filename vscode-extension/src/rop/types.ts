/**
 * VS Code bridge failure types for the PPI extension.
 *
 * Each bridge operation (settings resolution, command build, process
 * spawn, progress decode, RPC startup, cancellation, webview handoff)
 * has a distinguishable typed failure.
 */

/**
 * Categories of bridge failures.
 */
export type BridgeFailureCategory =
  | "settings"
  | "command"
  | "spawn"
  | "progress"
  | "rpc"
  | "cancellation"
  | "webview"
  | "unknown";

/**
 * Typed bridge failure for VS Code extension operations.
 */
export interface BridgeFailure {
  readonly category: BridgeFailureCategory;
  readonly stage: string;
  readonly message: string;
  readonly safeInputId: string;
  readonly cause?: unknown;
}

/**
 * Build a typed BridgeFailure.
 */
export function bridgeFailure(
  category: BridgeFailureCategory,
  stage: string,
  message: string,
  cause?: unknown,
): BridgeFailure {
  return {
    category,
    stage,
    message,
    safeInputId: "",
    cause,
  };
}
