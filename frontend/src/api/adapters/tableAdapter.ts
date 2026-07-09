/**
 * Adapter: /api/v1/tables/{tableId} DTO -> generic TableProjection.
 *
 * The adapter normalizes column and row action shapes so generic code
 * never has to know about generated DTO wrappers.
 *
 * Generic column normalization (T100):
 *   - valueType is lowercased and validated against the allowed set
 *   - default sort/visibility are preserved from the DTO
 *
 * Generic row action normalization (T101):
 *   - action.kind defaults to "drilldown"
 *   - targetTableId is preserved; params are passed through unchanged
 */
import type { TableColumnDefinition, TableProjection } from "../../domain/table";
import type { ActionDefinition } from "../../domain/action";
import type { ValueFormat } from "../../domain/metric";

const ALLOWED_VALUE_TYPES: ReadonlySet<TableColumnDefinition["valueType"]> = new Set([
  "string", "number", "integer", "boolean", "date", "datetime", "metric", "entity", "json",
]);

const ALLOWED_FORMAT_KINDS: ReadonlySet<NonNullable<ValueFormat>["kind"]> = new Set([
  "integer", "decimal", "compact", "percent", "datetime", "text",
]);

type ColumnDto = {
  id?: string;
  label?: string;
  valueType?: string;
  metricId?: string | null;
  format?: { kind?: string; precision?: number | null } | null;
  sortable?: boolean;
  visibleByDefault?: boolean;
  align?: "left" | "right" | "center";
  width?: number | null;
};

type RowActionDto = {
  id?: string;
  label?: string;
  kind?: string;
  targetTableId?: string | null;
  params?: Record<string, unknown>;
};

type RowDto = { id?: string; cells?: Record<string, unknown>; actions?: RowActionDto[] };

type Dto = {
  tableId?: string;
  title?: string;
  commitId?: string | null;
  columns?: ColumnDto[];
  rows?: RowDto[];
};

function adaptFormat(format: ColumnDto["format"]): ValueFormat | null {
  if (!format) return null;
  const kind = format.kind;
  if (!kind || !ALLOWED_FORMAT_KINDS.has(kind as NonNullable<ValueFormat>["kind"])) {
    return { kind: "text" };
  }
  return { kind: kind as NonNullable<ValueFormat>["kind"], precision: format.precision ?? null };
}

export function adaptTable(dto: Dto): TableProjection {
  return {
    tableId: dto.tableId ?? "unknown",
    title: dto.title ?? dto.tableId ?? "Table",
    commitId: dto.commitId ?? null,
    columns: (dto.columns ?? []).map(adaptColumn),
    rows: (dto.rows ?? []).map((r) => ({
      id: r.id ?? JSON.stringify(r.cells ?? {}),
      cells: r.cells ?? {},
      actions: (r.actions ?? []).map(adaptAction),
    })),
  };
}

export function adaptColumn(c: ColumnDto): TableColumnDefinition {
  const rawType = String(c.valueType ?? "string").toLowerCase();
  const valueType: TableColumnDefinition["valueType"] = (
    ALLOWED_VALUE_TYPES.has(rawType as TableColumnDefinition["valueType"]) ? rawType : "string"
  ) as TableColumnDefinition["valueType"];
  return {
    id: c.id ?? "unknown",
    label: c.label ?? c.id ?? "Unknown",
    valueType,
    metricId: c.metricId ?? null,
    format: adaptFormat(c.format),
    sortable: c.sortable ?? true,
    visibleByDefault: c.visibleByDefault ?? true,
    align: c.align ?? "left",
    width: c.width ?? null,
  };
}

export function adaptAction(a: RowActionDto): ActionDefinition {
  const kind = (a.kind as ActionDefinition["kind"]) ?? "drilldown";
  return {
    id: a.id ?? "unknown",
    label: a.label ?? a.id ?? "Action",
    kind,
    targetTableId: a.targetTableId ?? null,
    params: a.params ?? {},
  };
}
