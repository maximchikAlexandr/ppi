import type { UiConfig } from "../uiConfigTypes";

/**
 * UiConfig where the only line category is one the rest of the app has
 * never seen. DefinitionRegistry must surface it via fallback labels
 * without crashing.
 */
export const unknownLineCategoryUiConfig: UiConfig = {
  schemaVersion: 1,
  profile: { id: "test.unknown_line_profile", label: "Unknown Line Profile", pluginIds: [] },
  plugins: [],
  capabilities: [
    { id: "graph", label: "Graph", enabled: true },
    { id: "tables", label: "Tables", enabled: true },
    { id: "metricsDashboard", label: "Dashboard", enabled: true },
    { id: "diagnostics", label: "Diagnostics", enabled: false },
  ],
  pages: [],
  entityKinds: [
    { id: "module", label: "Module", pluralLabel: "Modules",
      description: null, icon: null, defaultTableId: null, supportedViews: ["graph", "table"] },
  ],
  metrics: [],
  relationTypes: [],
  lineCategories: [
    { id: "test.fremium_line", label: "Fremium Lines", defaultVisible: true, order: 0 },
  ],
  visualEncodings: [],
  graphLenses: [],
  tables: [],
  queries: [],
};
