/**
 * Dashboard view-model derivation tests.
 *
 * Covers valid, empty, and partial data scenarios.
 */

import { describe, it, expect } from "vitest";

import {
  computeMetrics,
  buildTableRows,
  buildTreemapNodes,
  buildDashboardViewModel,
} from "./dashboardViewModel";

import {
  validSnapshot,
  emptySnapshot,
  partialSnapshot,
} from "../api/__fixtures__/analysisResponses";

describe("dashboardViewModel", () => {
  describe("computeMetrics", () => {
    it("computes correct summary for valid snapshot", () => {
      const summary = computeMetrics(validSnapshot);
      expect(summary.totalModules).toBe(2);
      expect(summary.totalLines).toBe(150);
      expect(summary.totalEdges).toBe(1);
    });

    it("returns zeroes for empty snapshot", () => {
      const summary = computeMetrics(emptySnapshot);
      expect(summary.totalModules).toBe(0);
      expect(summary.totalLines).toBe(0);
    });
  });

  describe("buildTableRows", () => {
    it("builds rows for each module", () => {
      const rows = buildTableRows(validSnapshot.modules);
      expect(rows).toHaveLength(2);
      expect(rows[0].moduleName).toBe("module_a");
      expect(rows[0].lines).toBe(100);
    });

    it("returns empty array for no modules", () => {
      const rows = buildTableRows([]);
      expect(rows).toHaveLength(0);
    });
  });

  describe("buildTreemapNodes", () => {
    it("builds nodes for each module", () => {
      const nodes = buildTreemapNodes(validSnapshot.modules);
      expect(nodes).toHaveLength(2);
    });
  });

  describe("buildDashboardViewModel", () => {
    it("builds full view model from valid data", () => {
      const vm = buildDashboardViewModel(validSnapshot);
      expect(vm.summary.totalModules).toBe(2);
      expect(vm.tableRows).toHaveLength(2);
      expect(vm.treemapNodes).toHaveLength(2);
    });

    it("handles partial (empty modules) data", () => {
      const vm = buildDashboardViewModel(partialSnapshot);
      expect(vm.summary.totalModules).toBe(0);
      expect(vm.tableRows).toHaveLength(0);
    });
  });
});
