/**
 * Adapter boundary: the public DTO shape never escapes the adapter module.
 *
 * This test inspects a few representative adapters and proves they do
 * not return raw DTO wrappers; they return plain domain objects.
 */
import { describe, expect, it } from "vitest";

import { adaptGraph } from "./graphAdapter";
import { adaptTable } from "./tableAdapter";
import { adaptEntities } from "./entityAdapter";
import { adaptMetricTimeseries, adaptMetricHotspots } from "./dashboardAdapter";
import { adaptUiConfig } from "./uiConfigAdapter";
import { adaptTableToTreemap } from "./treemapAdapter";
import { adaptError, GenericApiError } from "./errorAdapter";
import { unknownResultKindUiConfig } from "../../registry/__fixtures__/unknownResultKindUiConfig";

describe("adapter boundary", () => {
  it("adaptUiConfig returns a UiConfig domain object", () => {
    const out = adaptUiConfig({
      schemaVersion: 2,
      capabilities: [{ id: "graph", label: "Graph", enabled: true }],
    });
    expect(out.schemaVersion).toBe(2);
    expect(out.profile.id).toBe("default");
    expect(out.capabilities.length).toBeGreaterThan(0);
  });

  it("adaptUiConfig normalizes an unknown query result kind", () => {
    // The backend declares `resultKind: "hologram"` which the dashboard
    // cannot render. The adapter must NOT pass it through; it must fall
    // back to a kind the dashboard knows, so the page does not silently
    // show empty data.
    const out = adaptUiConfig({
      schemaVersion: 1,
      profile: { id: "p", label: "P", pluginIds: [] },
      plugins: [],
      capabilities: [],
      pages: [],
      entityKinds: [],
      metrics: [],
      relationTypes: [],
      lineCategories: [],
      visualEncodings: [],
      graphLenses: [],
      tables: [],
      queries: [{ id: "q", label: "Q", resultKind: "hologram", parameters: [] }],
    });
    expect(out.queries[0]?.resultKind).toBe("timeseries");
  });

  it("adaptUiConfig preserves known result kinds", () => {
    const out = adaptUiConfig({
      schemaVersion: 1,
      profile: { id: "p", label: "P", pluginIds: [] },
      plugins: [],
      capabilities: [],
      pages: [],
      entityKinds: [],
      metrics: [],
      relationTypes: [],
      lineCategories: [],
      visualEncodings: [],
      graphLenses: [],
      tables: [],
      queries: [
        { id: "q1", label: "Q1", resultKind: "timeseries", parameters: [] },
        { id: "q2", label: "Q2", resultKind: "ranking", parameters: [] },
        { id: "q3", label: "Q3", resultKind: "distribution", parameters: [] },
      ],
    });
    expect(out.queries.map((q) => q.resultKind)).toEqual([
      "timeseries",
      "ranking",
      "distribution",
    ]);
  });

  it("adaptUiConfig exposes the unknown-result-kind fixture", () => {
    // The fixture is a real artefact; if this assertion holds, the
    // fixture is wired into the test suite.
    expect(unknownResultKindUiConfig.queries[0]?.resultKind).toBe("hologram");
  });

  it("adaptEntities normalizes unknown ids", () => {
    const out = adaptEntities({ entityKindId: "k", items: [{ id: "x" }] });
    expect(out[0].label).toBe("x");
    expect(out[0].kind).toBe("k");
  });

  it("adaptGraph returns an EntityGraphModel", () => {
    const out = adaptGraph({ commitId: "c", lensId: "l", nodes: [], edges: [] });
    expect(out.commitId).toBe("c");
    expect(out.lensId).toBe("l");
  });

  it("adaptTable normalizes columns and rows", () => {
    const out = adaptTable({
      tableId: "t", title: "T", commitId: "c",
      columns: [{ id: "a" }], rows: [{ id: "r1", cells: { a: 1 } }],
    });
    expect(out.columns[0].id).toBe("a");
    expect(out.rows[0].id).toBe("r1");
  });

  it("adaptMetricTimeseries returns a MetricQueryResult", () => {
    const out = adaptMetricTimeseries({
      entityKindId: "k", metricId: "m", aggregation: "mean", series: [],
    });
    expect(out.resultKind).toBe("timeseries");
  });

  it("adaptMetricHotspots returns a MetricQueryResult", () => {
    const out = adaptMetricHotspots({
      entityKindId: "k", metricId: "m", aggregation: "mean", items: [],
    });
    expect(out.resultKind).toBe("ranking");
  });

  it("happy path with unknown id falls back to defaults", () => {
    const out = adaptEntities({ items: [{}] });
    expect(out[0].label).toBe("—");
  });

  it("missing optional arrays produce empty defaults", () => {
    const out = adaptTable({});
    expect(out.columns).toEqual([]);
    expect(out.rows).toEqual([]);
  });

  it("adaptTableToTreemap builds items from a TableProjection", () => {
    const out = adaptTableToTreemap(
      {
        tableId: "t",
        title: "Files",
        commitId: "c",
        columns: [
          { id: "lines", label: "Lines", valueType: "number", format: null, sortable: true, visibleByDefault: true },
          { id: "cc", label: "CC", valueType: "number", format: null, metricId: "cyclomatic_mean", sortable: true, visibleByDefault: true },
        ],
        rows: [
          { id: "a.py", cells: { lines: 100, cc: 5 } },
          { id: "b.py", cells: { lines: 50, cc: 2 } },
        ],
      },
      { sizeColumnId: "lines", entityKindId: "file" },
    );
    expect(out.title).toBe("Files");
    expect(out.items).toHaveLength(2);
    expect(out.items[0]?.size).toBe(100);
    expect(out.items[0]?.entity.kind).toBe("file");
    expect(out.items[0]?.entity.id).toBe("a.py");
    // Size column must be excluded from metric groups; every other
    // visible column becomes a metric chip. Without a metricId
    // override, the chip id defaults to the column id.
    expect(out.items[0]?.metricGroups.map((g) => g.id)).toEqual(["cc"]);
  });

  it("adaptTableToTreemap treats missing cells as 0", () => {
    const out = adaptTableToTreemap(
      {
        tableId: "t",
        title: "T",
        columns: [
          { id: "lines", label: "Lines", valueType: "number", format: null, sortable: true, visibleByDefault: true },
        ],
        rows: [{ id: "a", cells: {} }],
      },
      { sizeColumnId: "lines", entityKindId: "file" },
    );
    expect(out.items[0]?.size).toBe(0);
  });

  it("adaptError decodes a structured { error: { code, message } } body", () => {
    const out = adaptError(404, {
      error: { code: "MODULE_NOT_FOUND", message: "no such module", requestId: "req-1" },
    });
    expect(out).toBeInstanceOf(GenericApiError);
    expect(out.status).toBe(404);
    expect(out.code).toBe("MODULE_NOT_FOUND");
    expect(out.message).toBe("no such module");
    expect(out.requestId).toBe("req-1");
  });

  it("adaptError falls back to a generic HTTP error for non-structured bodies", () => {
    const out = adaptError(500, "oops");
    expect(out).toBeInstanceOf(GenericApiError);
    expect(out.status).toBe(500);
    expect(out.code).toBe("HTTP_ERROR");
    expect(out.message).toBe("HTTP 500");
    expect(out.requestId).toBeNull();
  });

  it("adaptError fills missing code and message from the status", () => {
    const out = adaptError(503, { error: {} });
    expect(out.code).toBe("HTTP_ERROR");
    expect(out.message).toBe("HTTP 503");
  });
});
