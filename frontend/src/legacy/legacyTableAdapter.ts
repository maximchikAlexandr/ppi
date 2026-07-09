/**
 * Adapter: legacy snapshot/table/files response -> generic TableProjection.
 */
import type { TableProjection } from "../domain/table";

type LegacyTableRow = { id?: string; cells: Record<string, unknown>; actions?: Record<string, boolean> };

export function legacySnapshotToGenericTables(
  tableId: string,
  title: string,
  commitId: string | null,
  columns: { id: string; label: string; valueType: string; sortable?: boolean; visibleByDefault?: boolean; align?: "left" | "right" | "center" }[],
  rows: readonly LegacyTableRow[],
): TableProjection {
  return {
    tableId,
    title,
    commitId,
    columns: columns.map((c) => ({
      id: c.id,
      label: c.label,
      valueType: (c.valueType as never) ?? "string",
      sortable: c.sortable ?? true,
      visibleByDefault: c.visibleByDefault ?? true,
      align: c.align ?? "left",
    })),
    rows: rows.map((r) => ({
      id: r.id ?? JSON.stringify(r.cells),
      cells: r.cells,
      actions: r.actions
        ? Object.entries(r.actions)
            .filter(([, enabled]) => enabled)
            .map(([id]) => ({ id, label: id, kind: "drilldown" as const }))
        : [],
    })),
  };
}
