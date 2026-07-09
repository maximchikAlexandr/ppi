import type { UiConfig } from "../uiConfigTypes";

export const unknownUiConfig: UiConfig = {
  schemaVersion: 1,
  profile: { id: "test.unknown", label: "Unknown Test", pluginIds: [] },
  plugins: [],
  capabilities: [
    { id: "graph", label: "Graph", enabled: true },
    { id: "tables", label: "Tables", enabled: true },
    { id: "metricsDashboard", label: "Dashboard", enabled: true },
    { id: "diagnostics", label: "Diagnostics", enabled: false },
  ],
  pages: [],
  entityKinds: [
    { id: "test.unknown_kind", label: "Unknown Kind", pluralLabel: "Unknown Kinds",
      description: null, icon: null, defaultTableId: null, supportedViews: ["graph", "table"] },
  ],
  metrics: [
    {
      id: "test.unknown_metric",
      label: "Unknown Metric",
      description: null,
      valueType: "number",
      unit: null,
      scope: "entity",
      entityKinds: ["test.unknown_kind"],
      supportedAggregations: ["mean"],
      defaultAggregation: "mean",
      supportedViews: ["dashboard"],
      higherIsWorse: false,
      format: null,
      pluginId: null,
    },
  ],
  relationTypes: [
    { id: "test.unknown_relation", label: "Unknown Relation",
      description: null, group: null, defaultVisible: true, pluginId: null },
  ],
  lineCategories: [
    { id: "test.unknown_line", label: "Unknown Line", defaultVisible: false, order: 0 },
  ],
  visualEncodings: [],
  graphLenses: [
    {
      id: "test.unknown_lens",
      label: "Unknown Lens",
      description: null,
      nodeKinds: ["test.unknown_kind"],
      relationTypes: ["test.unknown_relation"],
      defaultVisualEncoding: {},
    },
  ],
  tables: [
    { id: "test.unknown_table", label: "Unknown Table",
      description: null, entityKindId: "test.unknown_kind",
      supportedActions: ["drilldown"], defaultSort: null },
  ],
  queries: [],
};
