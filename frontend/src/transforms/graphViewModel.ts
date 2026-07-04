/**
 * Graph view-model derivation pipeline.
 *
 * Pure typed stages: normalize graph snapshot -> calculate edge labels
 * -> filter/sort visible edges -> derive detail rows -> calculate viewport.
 *
 * No React dependencies — testable outside components.
 */

import type {
  AnalysisSnapshot,
  EdgeRow,
} from "../api/__fixtures__/analysisResponses";

/** Graph view model */
export interface GraphViewModel {
  readonly nodes: ReadonlyArray<GraphNode>;
  readonly edges: ReadonlyArray<GraphEdge>;
  readonly detailRows: ReadonlyArray<DetailRow>;
}

export interface GraphNode {
  readonly id: string;
  readonly label: string;
}

export interface GraphEdge {
  readonly source: string;
  readonly target: string;
  readonly label: string;
  readonly weight: number;
}

export interface DetailRow {
  readonly source: string;
  readonly target: string;
  readonly kinds: string;
  readonly score: number;
}

/**
 * Extract unique nodes from edges.
 */
export function extractNodes(edges: ReadonlyArray<EdgeRow>): ReadonlyArray<GraphNode> {
  const seen = new Set<string>();
  const nodes: Array<GraphNode> = [];
  for (const edge of edges) {
    if (!seen.has(edge.source)) {
      seen.add(edge.source);
      nodes.push({ id: edge.source, label: edge.source });
    }
    if (!seen.has(edge.target)) {
      seen.add(edge.target);
      nodes.push({ id: edge.target, label: edge.target });
    }
  }
  return nodes;
}

/**
 * Convert raw edges to graph edges with labels.
 */
export function calculateEdgeLabels(
  edges: ReadonlyArray<EdgeRow>,
): ReadonlyArray<GraphEdge> {
  return edges.map((e) => ({
    source: e.source,
    target: e.target,
    label: Object.keys(e.kinds).join(", "),
    weight: e.score,
  }));
}

/**
 * Filter and sort visible edges (exclude zero-score edges).
 */
export function filterSortVisibleEdges(
  edges: ReadonlyArray<GraphEdge>,
): ReadonlyArray<GraphEdge> {
  return edges
    .filter((e) => e.weight > 0)
    .sort((a, b) => b.weight - a.weight);
}

/**
 * Derive detail rows for the edge table.
 */
export function deriveDetailRows(
  edges: ReadonlyArray<EdgeRow>,
): ReadonlyArray<DetailRow> {
  return edges.map((e) => ({
    source: e.source,
    target: e.target,
    kinds: Object.keys(e.kinds).join(", "),
    score: e.score,
  }));
}

/**
 * Build a complete graph view model from a snapshot.
 */
export function buildGraphViewModel(
  snapshot: AnalysisSnapshot,
): GraphViewModel {
  const graphEdges = calculateEdgeLabels(snapshot.edges);
  return {
    nodes: extractNodes(snapshot.edges),
    edges: filterSortVisibleEdges(graphEdges),
    detailRows: deriveDetailRows(snapshot.edges),
  };
}
