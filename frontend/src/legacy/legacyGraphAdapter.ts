/**
 * Adapter: legacy module-shaped graph -> generic EntityGraphModel.
 *
 * Generic code must consume the output of this adapter only.
 */
import type { EntityGraphModel } from "../domain/graph";
import type { LegacyGraphEdge, LegacyGraphNode } from "./legacyApiTypes";

const PYTHON_MODULE_KIND = "python.module";

export function legacyGraphToGenericGraph(
  commitId: string,
  lensId: string,
  nodes: readonly LegacyGraphNode[],
  edges: readonly LegacyGraphEdge[],
): EntityGraphModel {
  return {
    commitId,
    lensId,
    nodes: nodes.map((n) => ({
      entity: {
        id: n.module_name,
        kind: PYTHON_MODULE_KIND,
        label: n.module_name,
      },
      metrics: Object.entries(n.metrics).map(([metricId, value]) => ({
        metricId,
        value,
        aggregation: null,
      })),
      lineCounts: n.line_counts ?? {},
    })),
    edges: edges.map((e) => ({
      id: `${e.source}->${e.target}`,
      source: { id: e.source, kind: PYTHON_MODULE_KIND, label: e.source },
      target: { id: e.target, kind: PYTHON_MODULE_KIND, label: e.target },
      relationTypeId: Object.keys(e.kinds)[0] ?? "imports",
      metrics: [{ metricId: "score", value: e.score, aggregation: null }],
    })),
  };
}
