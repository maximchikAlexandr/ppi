import { describe, it, expect } from "vitest";

import {
  buildFileTargetName,
  normalizeDashboardSelection,
  resolveMetric,
  resolveTarget,
  validMetricsForLevel,
  type MetricOption,
} from "./dashboardTransforms";

const metrics: readonly MetricOption[] = [
  { id: "cyclomatic", label: "Cyclomatic", supportedLevels: new Set(["module", "file"]) },
  { id: "lines", label: "Total lines", supportedLevels: new Set(["module", "file"]) },
  { id: "python_file_count", label: "Python file count", supportedLevels: new Set(["module"]) },
  { id: "function_count", label: "Function count", supportedLevels: new Set(["file"]) },
];

describe("validMetricsForLevel", () => {
  it("returns metrics supporting module level", () => {
    expect(validMetricsForLevel(metrics, "module")).toEqual(["cyclomatic", "lines", "python_file_count"]);
  });
  it("returns metrics supporting file level", () => {
    expect(validMetricsForLevel(metrics, "file")).toEqual(["cyclomatic", "lines", "function_count"]);
  });
});

describe("resolveMetric", () => {
  it("keeps current metric when valid for level", () => {
    expect(resolveMetric("cyclomatic", metrics, "file")).toBe("cyclomatic");
  });
  it("replaces metric when invalid for level", () => {
    expect(resolveMetric("python_file_count", metrics, "file")).toBe("cyclomatic");
  });
  it("returns null when no valid metrics exist", () => {
    expect(resolveMetric("anything", [], "file")).toBeNull();
  });
});

describe("resolveTarget", () => {
  it("keeps current target when valid", () => {
    expect(resolveTarget("m1", ["m1", "m2"])).toBe("m1");
  });
  it("replaces invalid target with first valid", () => {
    expect(resolveTarget("missing", ["m1", "m2"])).toBe("m1");
  });
  it("returns null when no targets exist", () => {
    expect(resolveTarget("m", [])).toBeNull();
  });
});

describe("normalizeDashboardSelection", () => {
  it("replaces module-only metric when level changes to file", () => {
    const result = normalizeDashboardSelection({
      level: "file",
      metric: "python_file_count",
      target: null,
      metrics,
      targets: ["module_a/path/a.py", "module_b/path/b.py"],
    });
    expect(result.metric).toBe("cyclomatic");
    expect(result.target).toBe("module_a/path/a.py");
    expect(result.isValid).toBe(true);
  });

  it("returns invalid when no valid target and no valid metric", () => {
    const result = normalizeDashboardSelection({
      level: "module",
      metric: null,
      target: null,
      metrics: [],
      targets: [],
    });
    expect(result.isValid).toBe(false);
  });

  it("returns invalid when only target missing", () => {
    const result = normalizeDashboardSelection({
      level: "module",
      metric: "cyclomatic",
      target: null,
      metrics,
      targets: [],
    });
    expect(result.isValid).toBe(false);
  });

  it("rejects module names as file targets during level switches", () => {
    const result = normalizeDashboardSelection({
      level: "file",
      metric: "cyclomatic",
      target: "module_a",
      metrics,
      targets: ["module_a", "module_b/models/b.py"],
    });
    expect(result.target).toBe("module_b/models/b.py");
    expect(result.isValid).toBe(true);
  });
});

describe("buildFileTargetName", () => {
  it("builds the module/relative/path name required by file timeseries", () => {
    expect(buildFileTargetName({ module_name: "module_a", relative_path: "models/a.py" })).toBe(
      "module_a/models/a.py",
    );
  });

  it("returns an empty target when a file row is incomplete", () => {
    expect(buildFileTargetName({ module_name: "module_a" })).toBe("");
  });
});
