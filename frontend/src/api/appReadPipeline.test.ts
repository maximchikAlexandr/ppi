/**
 * App read pipeline tests.
 *
 * Covers: successful composition, transport error propagation,
 * and schema decode failure.
 */

import { describe, it, expect, vi } from "vitest";
import { Effect } from "effect";

import { appReadPipeline } from "./appReadPipeline";
import { validRpcResponse, malformedJsonResponse } from "./__fixtures__/analysisResponses";

describe("appReadPipeline", () => {
  it("composes stages successfully for a valid response", async () => {
    const mockFetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(validRpcResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    try {
      const result = await Effect.runPromise(
        appReadPipeline({
          rpcUrl: "/api/rpc",
          method: "get_snapshot",
          params: { commit_hash: "abc" },
        }),
      );
      expect(result.commit_hash).toBe("abc123");
    } finally {
      mockFetch.mockRestore();
    }
  });

  it("fails with transport error on HTTP 500", async () => {
    const mockFetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("Internal Server Error", { status: 500 }),
    );

    try {
      const effect = appReadPipeline({
        rpcUrl: "/api/rpc",
        method: "get_snapshot",
        params: { commit_hash: "abc" },
      });
      const result = await Effect.runPromise(Effect.flip(effect));
      expect(result.category).toBe("transport");
    } finally {
      mockFetch.mockRestore();
    }
  });

  it("fails with schema error on malformed JSON", async () => {
    const mockFetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(malformedJsonResponse, {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    try {
      const effect = appReadPipeline({
        rpcUrl: "/api/rpc",
        method: "get_snapshot",
        params: { commit_hash: "abc" },
      });
      const result = await Effect.runPromise(Effect.flip(effect));
      expect(result.category).toBe("schema");
    } finally {
      mockFetch.mockRestore();
    }
  });
});
