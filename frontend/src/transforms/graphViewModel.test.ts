/**
 * Graph view-model derivation tests.
 *
 * Covers valid graph, empty graph, and invalid edge data.
 */

import { describe, it, expect } from "vitest";

import {
  extractNodes,
  calculateEdgeLabels,
  filterSortVisibleEdges,
  deriveDetailRows,
  buildGraphViewModel,
} from "./graphViewModel";

import {
  validSnapshot,
  emptySnapshot,
  invalidEdgeData,
} from "../api/__fixtures__/analysisResponses";

describe("graphViewModel", () => {
  describe("extractNodes", () => {
    it("extracts unique nodes from edges", () => {
      const nodes = extractNodes(validSnapshot.edges);
      expect(nodes).toHaveLength(2);
      expect(nodes[0].id).toBe("module_a");
      expect(nodes[1].id).toBe("module_b");
    });

    it("returns empty array for empty edges", () => {
      const nodes = extractNodes([]);
      expect(nodes).toHaveLength(0);
    });
  });

  describe("calculateEdgeLabels", () => {
    it("converts raw edges to graph edges", () => {
      const edges = calculateEdgeLabels(validSnapshot.edges);
      expect(edges).toHaveLength(1);
      expect(edges[0].weight).toBe(3);
    });
  });

  describe("filterSortVisibleEdges", () => {
    it("removes zero-weight edges", () => {
      const edges = calculateEdgeLabels(invalidEdgeData.edges);
      expect(edges).toHaveLength(1);
    });
  });

  describe("buildGraphViewModel", () => {
    it("builds full view model from valid data", () => {
      const vm = buildGraphViewModel(validSnapshot);
      expect(vm.nodes).toHaveLength(2);
      expect(vm.edges).toHaveLength(1);
    });

    it("handles empty graph", () => {
      const vm = buildGraphViewModel(emptySnapshot);
      expect(vm.nodes).toHaveLength(0);
      expect(vm.edges).toHaveLength(0);
    });
  });
});
