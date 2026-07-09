/// <reference types="vitest" />
import { describe, expect, it, vi, beforeEach } from "vitest";

const { fakeGet } = vi.hoisted(() => ({ fakeGet: vi.fn() }));

vi.mock("../api/http", () => ({
  publicHttp: {
    GET: fakeGet,
  },
  internalHttp: {
    GET: fakeGet,
  },
  ApiResult: class {},
}));

import { getStatusV1, getUiConfigV1, listEntitiesV1, listCommitsV1, getGraphV1, listTablesV1, getTableV1 } from "./publicApi";

function ok<T>(data: T) {
  return { data, error: undefined, response: { status: 200 } };
}

beforeEach(() => {
  fakeGet.mockReset();
  fakeGet.mockImplementation((path: string) => {
    if (path === "/api/v1/status") {
      return Promise.resolve(ok({
        projectId: "p1", branch: "main", storePresent: true, writerActive: false,
        commitCount: 1, apiStatus: "experimental",
      }));
    }
    if (path === "/api/v1/ui/config") {
      return Promise.resolve(ok({
        schemaVersion: 1,
        profile: { id: "default", label: "Default", pluginIds: [] },
        capabilities: [{ id: "graph", label: "Graph", enabled: true }],
        pages: [], entityKinds: [],
        metrics: [
          { id: "lines", label: "Lines", valueType: "integer", scope: "entity",
            entityKinds: ["python.module"], supportedAggregations: ["mean"],
            defaultAggregation: "mean", supportedViews: ["dashboard"] },
        ],
        relationTypes: [], lineCategories: [],
        visualEncodings: [], graphLenses: [],
        tables: [], queries: [],
      }));
    }
    if (path === "/api/v1/commits") {
      return Promise.resolve(ok({ items: [{ commitId: "c1", commitOrder: 1, authoredAt: null, summary: null }] }));
    }
    if (path === "/api/v1/entities") {
      return Promise.resolve(ok({
        entityKindId: "python.module",
        items: [{
          id: "m1", kind: "python.module", label: "m1", path: null, pluginId: null,
          selectable: true, reason: null,
        }],
      }));
    }
    if (path === "/api/v1/tables") {
      return Promise.resolve(ok({ items: [{ id: "t1", label: "T1" }] }));
    }
    if (path === "/api/v1/tables/{tableId}") {
      return Promise.resolve(ok({ tableId: "t1", title: "T1", commitId: null, columns: [], rows: [] }));
    }
    if (path === "/api/v1/graph") {
      return Promise.resolve(ok({ commitId: "c", lensId: "l", nodes: [], edges: [] }));
    }
    return Promise.resolve({ data: undefined, error: { error: { code: "NOT_FOUND", message: "not found" } }, response: { status: 404 } });
  });
});

describe("publicApi facade", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("getStatusV1 returns camelCase domain fields", async () => {
    const out = await getStatusV1();
    expect(out.projectId).toBe("p1");
    expect(out.branch).toBe("main");
    expect(out.storePresent).toBe(true);
    expect(out.apiStatus).toBe("experimental");
  });

  it("getUiConfigV1 returns domain fields, not raw DTO wrapper", async () => {
    const out = await getUiConfigV1();
    expect(out.schemaVersion).toBe(1);
    expect(out.profile.id).toBe("default");
    expect(Array.isArray(out.metrics)).toBe(true);
  });

  it("listEntitiesV1 returns EntityTarget[]", async () => {
    const out = await listEntitiesV1({ entityKindId: "python.module" });
    expect(out[0].id).toBe("m1");
    expect(out[0].kind).toBe("python.module");
  });

  it("listCommitsV1 returns CommitSummaryV1[]", async () => {
    const out = await listCommitsV1();
    expect(out[0].commitId).toBe("c1");
    expect(out[0].commitOrder).toBe(1);
  });

  it("getTableV1 returns a TableProjection", async () => {
    const out = await getTableV1({ tableId: "t1" });
    expect(out.tableId).toBe("t1");
    expect(out.title).toBe("T1");
    expect(out.columns).toEqual([]);
    expect(out.rows).toEqual([]);
  });

  it("getGraphV1 returns an EntityGraphModel", async () => {
    const out = await getGraphV1({ lensId: "l" });
    expect(out.commitId).toBe("c");
    expect(out.lensId).toBe("l");
  });

  it("listTablesV1 returns [{id,label}]", async () => {
    const out = await listTablesV1();
    expect(out[0].id).toBe("t1");
  });
});
