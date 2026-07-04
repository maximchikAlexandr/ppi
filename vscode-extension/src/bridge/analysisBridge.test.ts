/**
 * Bridge adapter tests for VS Code analysis progress decoding.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { Effect } from "effect";

import { decodeProgressEvent } from "./progressDecode";

describe("analysisBridge", () => {
  describe("decodeProgressEvent", () => {
    it("decodes a valid progress event", async () => {
      const event: { stage: string; status: string } = await Effect.runPromise(
        decodeProgressEvent(
          JSON.stringify({
            stage: "test",
            status: "running",
            message: "Working",
          }),
        ),
      );
      assert.equal(event.stage, "test");
      assert.equal(event.status, "running");
    });

    it("fails for invalid JSON", async () => {
      const result = decodeProgressEvent("not json");
      const exit = await Effect.runPromiseExit(result);
      assert.equal(exit._tag, "Failure");
    });

    it("fails for missing required fields", async () => {
      const result = decodeProgressEvent(JSON.stringify({ foo: "bar" }));
      const exit = await Effect.runPromiseExit(result);
      assert.equal(exit._tag, "Failure");
    });
  });
});
