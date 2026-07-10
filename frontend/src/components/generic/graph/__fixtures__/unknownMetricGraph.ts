import type { EntityGraphModel } from "../../../../domain/graph";

/**
 * A graph whose nodes and edges carry metrics and relation types that
 * are not in the default registry (the "fremium_metric" and
 * "fremium_relation" ids below do not appear in the standard
 * UiConfig). Generic graph components must render this without any
 * code change.
 */
export const unknownMetricGraph: EntityGraphModel = {
  commitId: "c-unknown-metric",
  lensId: "test.lens_with_unknown_metric",
  nodes: [
    {
      entity: { id: "pkg-alpha", kind: "package", label: "pkg-alpha" },
      metrics: [
        { metricId: "fremium_metric", value: 73 },
      ],
    },
    {
      entity: { id: "pkg-beta", kind: "package", label: "pkg-beta" },
      metrics: [
        { metricId: "fremium_metric", value: 41 },
      ],
    },
  ],
  edges: [
    {
      id: "pkg-alpha->pkg-beta",
      source: { id: "pkg-alpha", kind: "package", label: "pkg-alpha" },
      target: { id: "pkg-beta", kind: "package", label: "pkg-beta" },
      relationTypeId: "fremium_relation",
      metrics: [
        { metricId: "fremium_edge_weight", value: 12 },
      ],
    },
  ],
};
