/**
 * Shared frontend fixture for valid and invalid API/RPC responses.
 *
 * Provides representative snapshots used by the API read pipeline
 * and view-model derivation tests during the ROP migration.
 */

/** Generic RPC response shape */
export interface RpcResponse<T> {
  readonly jsonrpc: "2.0";
  readonly id: number;
  readonly result?: T;
  readonly error?: RpcError;
}

interface RpcError {
  readonly code: number;
  readonly message: string;
  readonly data?: unknown;
}

/** Minimal analysis snapshot shape used by dashboard/graph */
export interface AnalysisSnapshot {
  readonly commit_hash: string;
  readonly modules: ReadonlyArray<ModuleRow>;
  readonly edges: ReadonlyArray<EdgeRow>;
  readonly failures: ReadonlyArray<FailureRow>;
}

export interface ModuleRow {
  readonly module_name: string;
  readonly total_lines: number;
  readonly metrics: Record<string, number>;
  readonly line_counts: Record<string, number>;
}

export interface EdgeRow {
  readonly source: string;
  readonly target: string;
  readonly score: number;
  readonly kinds: Record<string, number>;
}

interface FailureRow {
  readonly commit_hash: string | null;
  readonly file_path: string | null;
  readonly error_text: string;
}

/** Valid snapshot with two modules and one edge */
export const validSnapshot: AnalysisSnapshot = {
  commit_hash: "abc123",
  modules: [
    {
      module_name: "module_a",
      total_lines: 100,
      metrics: { cyclomatic_mean: 2.5, cognitive_mean: 1.2 },
      line_counts: { python_lines: 80, xml_lines: 20 },
    },
    {
      module_name: "module_b",
      total_lines: 50,
      metrics: { cyclomatic_mean: 3.0, cognitive_mean: 2.0 },
      line_counts: { python_lines: 40, xml_lines: 10 },
    },
  ],
  edges: [
    {
      source: "module_a",
      target: "module_b",
      score: 3,
      kinds: { python_inherit: 2, python_method_call: 1 },
    },
  ],
  failures: [],
};

/** Valid RPC response */
export const validRpcResponse: RpcResponse<AnalysisSnapshot> = {
  jsonrpc: "2.0",
  id: 1,
  result: validSnapshot,
};

/** Schema error response (malformed RPC) */
export const schemaErrorResponse: RpcResponse<unknown> = {
  jsonrpc: "2.0",
  id: 2,
  error: {
    code: -32700,
    message: "Parse error",
    data: "Invalid JSON",
  },
};

/** Partial data snapshot (missing fields) */
export const partialSnapshot: AnalysisSnapshot = {
  commit_hash: "def456",
  modules: [],
  edges: [],
  failures: [],
};

/** Invalid edge data (negative score) */
export const invalidEdgeData: AnalysisSnapshot = {
  commit_hash: "ghi789",
  modules: [],
  edges: [
    {
      source: "module_a",
      target: "module_b",
      score: -1,
      kinds: {},
    },
  ],
  failures: [],
};

/** Malformed JSON (not parseable) */
export const malformedJsonResponse = "not valid json";

/** Empty snapshot for edge cases */
export const emptySnapshot: AnalysisSnapshot = {
  commit_hash: "",
  modules: [],
  edges: [],
  failures: [],
};
