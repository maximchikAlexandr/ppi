import type { MetricId, EntityKindId } from "./ids";

export type ValueFormat =
  | { kind: "integer"; precision?: number | null }
  | { kind: "decimal"; precision?: number | null }
  | { kind: "compact"; precision?: number | null }
  | { kind: "percent"; precision?: number | null }
  | { kind: "datetime" }
  | { kind: "text" };

export type MetricValueType =
  | "number"
  | "integer"
  | "ratio"
  | "duration"
  | "string"
  | "boolean";

export type MetricScope =
  | "entity"
  | "relation"
  | "graph"
  | "table"
  | "project"
  | string;

export type MetricDefinition = {
  id: MetricId;
  label: string;
  description?: string | null;
  valueType: MetricValueType;
  unit?: string | null;
  scope: MetricScope;
  entityKinds: EntityKindId[];
  supportedAggregations: string[];
  defaultAggregation?: string | null;
  supportedViews: string[];
  higherIsWorse?: boolean | null;
  format?: ValueFormat | null;
  pluginId?: string | null;
};

export type MetricValue = {
  metricId: MetricId;
  value: number | string | boolean | null;
  aggregation?: string | null;
};

export type MetricDistribution = {
  metricId: MetricId;
  values: {
    count?: number;
    mean?: number;
    median?: number;
    p95?: number;
    max?: number;
  };
};
