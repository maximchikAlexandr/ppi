import type { TableId } from "./ids";

export type ActionDefinition = {
  id: string;
  label: string;
  kind: "drilldown" | "navigate" | "select";
  targetTableId?: TableId | null;
  params?: Record<string, unknown>;
};

export type TableRowAction = ActionDefinition;

export type ActionParamKind = "string" | "number" | "boolean" | "entityId";

export type ActionParamDefinition = {
  id: string;
  kind: ActionParamKind;
  required: boolean;
};
