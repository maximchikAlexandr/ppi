/**
 * API/RPC read pipeline tests.
 *
 * Covers: valid response, transport error, schema error, and mapping error.
 */

import { describe, it, expect } from "vitest";
import { Effect } from "effect";

import {
  buildRequest,
  decodeResponse,
  mapDtoToDomain,
} from "./readPipeline";

import { validRpcResponse, schemaErrorResponse } from "./__fixtures__/analysisResponses";

describe("readPipeline", () => {
  describe("buildRequest", () => {
    it("produces a valid JSON-RPC request string", () => {
      const request = buildRequest("get_snapshot", { commit_hash: "abc" });
      const parsed = JSON.parse(request);
      expect(parsed.jsonrpc).toBe("2.0");
      expect(parsed.method).toBe("get_snapshot");
      expect(parsed.params.commit_hash).toBe("abc");
    });
  });

  describe("decodeResponse", () => {
    it("succeeds for valid RPC response JSON", async () => {
      const raw = JSON.stringify(validRpcResponse);
      const result = await Effect.runPromise(decodeResponse(raw));
      expect(result.jsonrpc).toBe("2.0");
    });

    it("fails for malformed JSON", async () => {
      const result = decodeResponse("not json");
      const exit = await Effect.runPromiseExit(result);
      expect(exit._tag).toBe("Failure");
    });
  });

  describe("mapDtoToDomain", () => {
    it("succeeds for valid RPC response with result", async () => {
      const result = await Effect.runPromise(
        mapDtoToDomain(validRpcResponse),
      );
      expect(result.commit_hash).toBe("abc123");
      expect(result.modules).toHaveLength(2);
    });

    it("fails for RPC error response", async () => {
      const result = mapDtoToDomain(schemaErrorResponse as any);
      const exit = await Effect.runPromiseExit(result);
      expect(exit._tag).toBe("Failure");
    });
  });
});
