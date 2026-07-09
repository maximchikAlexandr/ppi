/**
 * Pure adapter: TableProjection -> TreemapProjection.
 *
 * The treemap needs a `size` number and a structured `metricGroups`
 * list. Tables expose cells as a `Record<string, unknown>`. This
 * adapter looks for a column tagged as the size metric and turns
 * every other column into a metric group.
 */
import type { TableProjection } from "../../domain/table";
import type { TreemapItem, TreemapProjection } from "../../domain/treemap";

export type TreemapSizeColumnId = string;
export type TreemapEntityKindId = string;

export function adaptTableToTreemap(
  table: TableProjection,
  args: {
    sizeColumnId: TreemapSizeColumnId;
    entityKindId: TreemapEntityKindId;
    /**
     * Optional mapping of column id -> metric id. Defaults to the
     * column id itself, which works for tables whose columns are
     * already metric ids.
     */
    metricIdByColumn?: Readonly<Record<string, string>>;
  },
): TreemapProjection {
  const { sizeColumnId, entityKindId, metricIdByColumn } = args;
  const items: TreemapItem[] = table.rows.map((row) => {
    const id = String(row.id ?? "");
    const cells = row.cells as Record<string, unknown>;
    const size = toNumber(cells[sizeColumnId]) ?? 0;
    const metricGroups = table.columns
      .filter((col) => col.id !== sizeColumnId && col.visibleByDefault)
      .map((col) => {
        const metricId = metricIdByColumn?.[col.id] ?? col.id;
        return {
          id: metricId,
          label: col.label,
          value: toScalar(cells[col.id]),
          unit: null,
          format: col.format ?? null,
        };
      });
    return {
      entity: { id: id as never, kind: entityKindId as never, label: id },
      size,
      colorMetricId: null,
      colorValue: null,
      group: null,
      metricGroups,
      attributes: {},
    };
  });
  return {
    title: table.title,
    items,
    defaultSelectedId: null,
  };
}

function toNumber(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function toScalar(v: unknown): number | string | null {
  if (v === null || v === undefined) return null;
  if (typeof v === "number" || typeof v === "string") {
    return v;
  }
  if (typeof v === "boolean") return v ? "true" : "false";
  return JSON.stringify(v);
}
