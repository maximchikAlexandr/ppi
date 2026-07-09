import type { TableProjection } from "../../../../domain/table";

export const genericTable: TableProjection = {
  tableId: "test.unknown_table",
  title: "Unknown Table",
  commitId: "c1",
  columns: [
    { id: "label", label: "Label", valueType: "string", sortable: true, visibleByDefault: true },
    { id: "size", label: "Size", valueType: "integer", sortable: true, visibleByDefault: true, align: "right" },
    { id: "weird_column", label: "Weird Column", valueType: "json", sortable: false, visibleByDefault: true },
  ],
  rows: [
    {
      id: "r1",
      cells: { label: "alpha", size: 12, weird_column: { foo: "bar" } },
      actions: [{
        id: "open",
        label: "Open",
        kind: "drilldown",
        targetTableId: "test.other_table",
        params: { id: "r1" },
      }],
    },
  ],
};
