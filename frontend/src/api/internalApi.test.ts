/// <reference types="vitest" />
import { describe, expect, it, vi } from "vitest";

const { fakeGet } = vi.hoisted(() => ({ fakeGet: vi.fn() }));

vi.mock("../api/http", () => ({
  publicHttp: { GET: fakeGet },
  internalHttp: { GET: fakeGet },
  ApiResult: class {},
}));

import { getLegacyGraph, getLegacySnapshotTableFiles, getLegacySnapshotTableModules } from "./internalApi";

describe("internalApi facade", () => {
  it("getLegacyGraph uses the typed openapi-fetch client", async () => {
    fakeGet.mockResolvedValueOnce({
      data: { commit_hash: "c1", nodes: [], edges: [] },
      error: undefined,
      response: { status: 200 },
    });
    const out = await getLegacyGraph("c1");
    expect((out as { commit_hash: string }).commit_hash).toBe("c1");
    expect(fakeGet).toHaveBeenCalledWith("/api/graph", expect.objectContaining({
      params: expect.objectContaining({
        query: expect.objectContaining({ commit: "c1" }),
      }),
    }));
  });

  it("getLegacySnapshotTableModules calls /api/snapshot/table/modules", async () => {
    fakeGet.mockResolvedValueOnce({ data: { rows: [] }, error: undefined, response: { status: 200 } });
    const out = await getLegacySnapshotTableModules("c1");
    expect((out as { rows: unknown[] }).rows).toEqual([]);
    expect(fakeGet).toHaveBeenCalledWith("/api/snapshot/table/modules", expect.anything());
  });

  it("getLegacySnapshotTableFiles calls /api/snapshot/table/files", async () => {
    fakeGet.mockResolvedValueOnce({ data: { rows: [] }, error: undefined, response: { status: 200 } });
    await getLegacySnapshotTableFiles("c1", "mod");
    expect(fakeGet).toHaveBeenCalledWith("/api/snapshot/table/files", expect.anything());
  });
});
