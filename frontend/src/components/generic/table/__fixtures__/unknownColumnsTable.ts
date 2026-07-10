import type { TableProjection } from "../../../../domain/table";

/**
 * A table whose columns reference metrics that the registry does not
 * know. Generic GenericDataTable must render numeric cells without
 * crashing; the registry falls back to formatting.
 */
export const unknownColumnsTable: TableProjection = {
  tableId: "test.fremium_table",
  commitId: "c",
  title: "Fremium columns",
  columns: [
    { id: "fremium_score", label: "Fremium Score", valueType: "number", format: { kind: "integer" }, metricId: "fremium_metric", visibleByDefault: true, sortable: true },
    { id: "fremium_pct", label: "Fremium %", valueType: "number", format: { kind: "percent" }, metricId: "fremium_pct", visibleByDefault: true, sortable: true },
    { id: "fremium_at", label: "Updated at", valueType: "string", format: { kind: "datetime" }, visibleByDefault: true, sortable: false },
  ],
  rows: [
    {
      id: "row-1",
      cells: { fremium_score: 88, fremium_pct: 0.42, fremium_at: "2026-01-02T00:00:00Z" },
      actions: [],
    },
    {
      id: "row-2",
      cells: { fremium_score: 17, fremium_pct: 0.07, fremium_at: "2026-02-14T00:00:00Z" },
      actions: [],
    },
  ],
};
