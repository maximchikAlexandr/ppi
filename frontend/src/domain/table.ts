import type { TableId } from "./ids";
import type { ValueFormat } from "./metric";
import type { ActionDefinition } from "./action";

export type TableSort = { columnId: string; direction: "asc" | "desc" };

export type TableDefinition = {
  id: TableId;
  label: string;
  description?: string | null;
  entityKindId?: string | null;
  supportedActions: string[];
  defaultSort?: TableSort | null;
};

export type TableColumnValueType =
  | "string"
  | "number"
  | "integer"
  | "boolean"
  | "date"
  | "datetime"
  | "metric"
  | "entity"
  | "json";

export type TableColumnDefinition = {
  id: string;
  label: string;
  valueType: TableColumnValueType;
  metricId?: string | null;
  format?: ValueFormat | null;
  sortable: boolean;
  visibleByDefault: boolean;
  align?: "left" | "right" | "center";
  width?: number | null;
};

export type TableRow = {
  id: string;
  cells: Record<string, unknown>;
  actions?: ActionDefinition[];
};

export type TableProjection = {
  tableId: TableId;
  title: string;
  commitId?: string | null;
  columns: TableColumnDefinition[];
  rows: TableRow[];
};

export type DrilldownFrame = {
  tableId: TableId;
  title: string;
  params: Record<string, unknown>;
};
