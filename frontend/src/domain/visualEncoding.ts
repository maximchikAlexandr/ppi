import type { MetricId } from "./ids";

export type VisualEncodingRole =
  | "size"
  | "color"
  | "brightness"
  | "thickness"
  | "badge"
  | "label";

export type VisualEncodingAppliesTo = "node" | "edge" | "table" | "dashboard";

export type VisualEncodingDefinition = {
  id: string;
  label: string;
  appliesTo: VisualEncodingAppliesTo;
  role: VisualEncodingRole;
  metricId?: MetricId | null;
  attributeId?: string | null;
  defaultSelected: boolean;
};
