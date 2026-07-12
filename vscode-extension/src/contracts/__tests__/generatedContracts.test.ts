import { describe, it } from "node:test";
import assert from "node:assert";

describe("generated contracts facade compile check", () => {
  it("errorCodes facade is importable", async () => {
    const mod = await import("../../contracts/errorCodes");
    assert.ok(mod.ErrorCode);
    assert.strictEqual(mod.ErrorCode.INVALID_REQUEST, "INVALID_REQUEST");
  });

  it("progressEvents facade is importable", async () => {
    const mod = await import("../../contracts/progressEvents");
    assert.strictEqual(typeof mod.validateProgressEvent, "function");
  });

  it("webviewProtocol facade is importable", async () => {
    const mod = await import("../../contracts/webviewProtocol");
    assert.ok(mod);
  });
});
