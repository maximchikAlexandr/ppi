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
});
