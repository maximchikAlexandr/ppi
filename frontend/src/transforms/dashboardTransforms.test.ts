import { describe, it, expect } from "vitest";

import {
  getValidMetricsForEntityKind,
  getValidAggregationsForMetric,
  normalizeMetricQueryState,
} from "./dashboardTransforms";
import type { MetricDefinition } from "../domain/metric";

function metric(id: string, entityKinds: string[], aggs: string[] = ["mean", "sum"]): MetricDefinition {
  return {
    id,
    label: id,
    unit: "",
    format: "number",
    entityKinds: entityKinds as MetricDefinition["entityKinds"],
    supportedAggregations: aggs,
    defaultAggregation: aggs[0] ?? "mean",
    supportedViews: ["graph", "table"],
    defaultVisible: true,
  };
}

const metrics: readonly MetricDefinition[] = [
  metric("python_lines", ["module"]),
  metric("cyclomatic_mean", ["module", "file"], ["mean", "max"]),
  metric("class_count", ["class"]),
];

describe("getValidMetricsForEntityKind", () => {
  it("returns metrics whose entityKinds include the requested kind", () => {
    const result = getValidMetricsForEntityKind(metrics, "module");
    expect(result.map((m) => m.id).sort()).toEqual(["cyclomatic_mean", "python_lines"]);
  });
  it("returns empty array for unknown kind", () => {
    expect(getValidMetricsForEntityKind(metrics, "function")).toEqual([]);
  });
});

describe("getValidAggregationsForMetric", () => {
  it("returns supported aggregations for a metric", () => {
    expect(getValidAggregationsForMetric(metrics[1]!)).toEqual(["mean", "max"]);
  });
  it("returns empty array for null metric", () => {
    expect(getValidAggregationsForMetric(null)).toEqual([]);
  });
});

describe("normalizeMetricQueryState", () => {
  it("rejects missing entity kind", () => {
    const result = normalizeMetricQueryState({
      entityKindId: null,
      targetId: null,
      metricId: null,
      aggregation: null,
      metrics,
    });
    expect(result).toEqual({ status: "unavailable", reason: "missing_entity_kind" });
  });
  it("rejects when no metrics exist for the entity kind", () => {
    const result = normalizeMetricQueryState({
      entityKindId: "function",
      targetId: null,
      metricId: "python_lines",
      aggregation: "mean",
      metrics,
    });
    expect(result).toEqual({ status: "unavailable", reason: "no_metrics_for_entity_kind" });
  });
  it("falls back to first valid metric when requested metric does not exist for the kind", () => {
    const result = normalizeMetricQueryState({
      entityKindId: "module",
      targetId: null,
      metricId: "jones",
      aggregation: "mean",
      metrics,
    });
    expect(result.status).toBe("valid");
    if (result.status === "valid") {
      expect(result.state.metricId).toBe("python_lines");
    }
  });
  it("rejects unknown aggregation", () => {
    const result = normalizeMetricQueryState({
      entityKindId: "module",
      targetId: null,
      metricId: "cyclomatic_mean",
      aggregation: "median",
      metrics,
    });
    expect(result).toEqual({ status: "unavailable", reason: "unknown_aggregation" });
  });
  it("rejects missing target when availableTargetIds is given", () => {
    const result = normalizeMetricQueryState({
      entityKindId: "module",
      targetId: "ghost",
      metricId: "python_lines",
      aggregation: "mean",
      metrics,
      availableTargetIds: new Set(["m1", "m2"]),
    });
    expect(result).toEqual({ status: "unavailable", reason: "missing_target" });
  });
  it("accepts valid combinations and returns the normalized state", () => {
    const result = normalizeMetricQueryState({
      entityKindId: "module",
      targetId: "m1",
      metricId: "cyclomatic_mean",
      aggregation: "max",
      metrics,
      availableTargetIds: new Set(["m1", "m2"]),
    });
    expect(result).toEqual({
      status: "valid",
      state: {
        entityKindId: "module",
        targetId: "m1",
        metricId: "cyclomatic_mean",
        aggregation: "max",
      },
    });
  });
  it("falls back to the metric's default aggregation when none requested", () => {
    const result = normalizeMetricQueryState({
      entityKindId: "module",
      targetId: null,
      metricId: "python_lines",
      aggregation: null,
      metrics,
    });
    expect(result.status).toBe("valid");
    if (result.status === "valid") {
      expect(result.state.aggregation).toBe("mean");
    }
  });
  it("narrows MetricQueryStateResult correctly across every unavailable reason", () => {
    // The DashboardPage switches on result.status; if a new reason is
    // added and never handled, the page would silently show no chart.
    // This test pins the exhaustive list so a missing branch is caught
    // by `tsc --noUnusedParameters` when consumed downstream.
    const reasons: Array<
      "missing_entity_kind" | "no_metrics_for_entity_kind" | "missing_aggregation" | "unknown_aggregation" | "missing_target"
    > = [
      "missing_entity_kind",
      "no_metrics_for_entity_kind",
      "missing_aggregation",
      "unknown_aggregation",
      "missing_target",
    ];
    expect(new Set(reasons)).toEqual(
      new Set([
        "missing_entity_kind",
        "no_metrics_for_entity_kind",
        "missing_aggregation",
        "unknown_aggregation",
        "missing_target",
      ]),
    );
  });
});
