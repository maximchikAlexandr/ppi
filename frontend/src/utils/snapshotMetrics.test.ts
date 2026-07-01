import { describe, expect, it } from "vitest";

import { lineCategoryValue, resolveSnapshotMetricValue, sumLineCounts } from "./snapshotMetrics";

describe("snapshotMetrics", () => {
  it("maps generic complexity ids to median snapshot fields", () => {
    expect(resolveSnapshotMetricValue({
      metricId: "cyclomatic",
      metrics: { cyclomatic_median: 3 },
    })).toBe(3);
    expect(resolveSnapshotMetricValue({
      metricId: "cognitive",
      metrics: { cognitive_median: 2 },
    })).toBe(2);
    expect(resolveSnapshotMetricValue({
      metricId: "jones",
      metrics: { jones_median: 4 },
    })).toBe(4);
  });

  it("reads count-like metrics from line_counts and total lines", () => {
    expect(resolveSnapshotMetricValue({
      metricId: "function_count",
      lineCounts: { function_count: 48 },
    })).toBe(48);
    expect(resolveSnapshotMetricValue({
      metricId: "jones_line_count",
      lineCounts: { jones_line_count: 388 },
    })).toBe(388);
    expect(resolveSnapshotMetricValue({
      metricId: "lines",
      totalLines: 501,
    })).toBe(501);
  });

  it("normalizes test_lines to python_test_lines", () => {
    expect(lineCategoryValue({ python_test_lines: 7 }, "test_lines")).toBe(7);
  });

  it("sums line count buckets for lines_by_category", () => {
    expect(sumLineCounts({ python_lines: 10, python_test_lines: 2, js_lines: 3 })).toBe(15);
    expect(resolveSnapshotMetricValue({
      metricId: "lines_by_category",
      lineCounts: { python_lines: 10, python_test_lines: 2, js_lines: 3 },
    })).toBe(15);
  });
});
