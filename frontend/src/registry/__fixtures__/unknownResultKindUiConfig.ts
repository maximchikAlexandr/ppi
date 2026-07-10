import type { UiConfig } from "../uiConfigTypes";

/**
 * UiConfig whose only query declares a resultKind that the dashboard
 * does not know. The adapter must normalize or fall back; it must
 * never pass the unknown kind through silently.
 *
 * `resultKind: "hologram"` is intentionally invalid against
 * `QueryResultKind`; the `as never` is what simulates the wire
 * shape (the backend may send any string; the adapter must
 * defend). This is a test fixture, not production code.
 */
export const unknownResultKindUiConfig: UiConfig = {
  schemaVersion: 1,
  profile: { id: "test.unknown_qk", label: "Unknown Result Kind", pluginIds: [] },
  plugins: [],
  capabilities: [
    { id: "graph", label: "Graph", enabled: true },
    { id: "tables", label: "Tables", enabled: true },
    { id: "metricsDashboard", label: "Dashboard", enabled: true },
    { id: "diagnostics", label: "Diagnostics", enabled: false },
  ],
  pages: [],
  entityKinds: [],
  metrics: [],
  relationTypes: [],
  lineCategories: [],
  visualEncodings: [],
  graphLenses: [],
  tables: [],
  queries: [
    {
      id: "test.hologram_query",
      label: "Hologram query",
      resultKind: "hologram" as never,
      parameters: [],
    },
  ],
};
