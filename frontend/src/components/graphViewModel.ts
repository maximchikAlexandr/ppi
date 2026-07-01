import type { GraphEdge, GraphNode } from "../api/client";
import { colorForComplexityRatio, strokeForComplexityRatio } from "../registry/graphUiHelpers";
import { resolveSnapshotMetricValue } from "../utils/snapshotMetrics";
import {
  buildGraphEdgeViews,
  computeNodeDisplay,
  maxLinkThicknessMetric,
  maxNodeMetric,
  type GraphEdgeViewModel,
  type NodeDisplayModel,
} from "./graphSelectors";
import type { GraphDisplayState } from "./graphSettingsTypes";

export type ModuleGraphViewModel = {
  readonly maxMetric: number;
  readonly thicknessMax: number;
  readonly nodeRadiiById: ReadonlyMap<string, number>;
  readonly edgeViews: readonly GraphEdgeViewModel[];
  readonly nodeDisplayById: ReadonlyMap<string, NodeDisplayModel>;
};

function nodeMetricValueForBrightness(
  node: GraphNode,
  metricId: string,
): number {
  if (metricId === "visible_lines") {
    return 0;
  }
  return resolveSnapshotMetricValue({
    metricId,
    metrics: node.metrics,
    lineCounts: node.line_counts,
    totalLines: node.total_lines,
  });
}

function computeBrightnessRatio(
  node: GraphNode,
  nodes: readonly GraphNode[],
  brightnessMetrics: readonly string[],
): number {
  if (!brightnessMetrics.length) {
    return 0;
  }
  let sum = 0;
  let count = 0;
  for (const metricId of brightnessMetrics) {
    const nodeValue = nodeMetricValueForBrightness(node, metricId);
    const maxValue = Math.max(
      0,
      ...nodes.map((candidate) => nodeMetricValueForBrightness(candidate, metricId)),
    );
    if (maxValue <= 0) {
      continue;
    }
    sum += nodeValue / maxValue;
    count += 1;
  }
  return count > 0 ? Math.max(0, Math.min(1, sum / count)) : 0;
}

export function buildModuleGraphViewModel(
  nodes: readonly GraphNode[],
  edges: readonly GraphEdge[],
  display: GraphDisplayState,
  enabledEdgeKinds: Readonly<Record<string, boolean>>,
  lineCategories: ReadonlySet<string>,
  selectedModule: string | null,
  hoveredId: string | null,
  labelZoom: number,
  badgeMetrics: readonly string[] = [],
): ModuleGraphViewModel {
  const maxMetric = maxNodeMetric(nodes, display.nodeSizeMetric, lineCategories);
  const thicknessMax = maxLinkThicknessMetric(edges, display, enabledEdgeKinds);

  const edgeViews = buildGraphEdgeViews(edges, display, enabledEdgeKinds, thicknessMax);

  const nodeRadiiById = new Map<string, number>();
  const nodeDisplayById = new Map<string, NodeDisplayModel>();
  for (const node of nodes) {
    const id = node.module_name;
    const ratio = computeBrightnessRatio(node, nodes, badgeMetrics);
    nodeRadiiById.set(
      id,
      computeNodeDisplay(node, display, {
        maxMetric,
        brightnessRatio: ratio,
        selected: false,
        hovered: false,
        lineCategories,
        fill: "",
        stroke: "",
        zoomScale: 1,
        badgeMetrics,
      }).radius,
    );
    nodeDisplayById.set(
      id,
      computeNodeDisplay(node, display, {
        maxMetric,
        brightnessRatio: ratio,
        selected: selectedModule === id,
        hovered: hoveredId === id,
        lineCategories,
        fill: colorForComplexityRatio(ratio),
        stroke: strokeForComplexityRatio(ratio),
        zoomScale: labelZoom,
        badgeMetrics,
      }),
    );
  }

  return {
    maxMetric,
    thicknessMax,
    nodeRadiiById,
    edgeViews,
    nodeDisplayById,
  };
}
