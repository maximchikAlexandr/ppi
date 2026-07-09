import type { EntityGraphModel } from "../../../../domain/graph";

export const nonModuleGraph: EntityGraphModel = {
  commitId: "c",
  lensId: "test.unknown_lens",
  nodes: [
    { entity: { id: "doc-1", kind: "doc.section", label: "Section 1" }, metrics: [] },
    { entity: { id: "doc-2", kind: "doc.section", label: "Section 2" }, metrics: [] },
  ],
  edges: [
    {
      id: "doc-1->doc-2",
      source: { id: "doc-1", kind: "doc.section", label: "Section 1" },
      target: { id: "doc-2", kind: "doc.section", label: "Section 2" },
      relationTypeId: "test.unknown_relation",
      metrics: [],
    },
  ],
};
