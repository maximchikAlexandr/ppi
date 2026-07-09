import type { EntityRef } from "./entity";
import type { MetricValue } from "./metric";
import type { MetricId, RelationTypeId } from "./ids";

export type RelationTypeDefinition = {
  id: RelationTypeId;
  label: string;
  description?: string | null;
  group?: string | null;
  defaultVisible: boolean;
  pluginId?: string | null;
};

export type RelationRecord = {
  id: string;
  source: EntityRef;
  target: EntityRef;
  relationTypeId: RelationTypeId;
  metrics: MetricValue[];
  attributes?: Record<string, unknown>;
};

export type RelationContribution = {
  typeId: string;
  metricId: MetricId;
  value: number;
};

export type LineCategoryDefinition = {
  id: string;
  label: string;
  defaultVisible: boolean;
  order: number;
};
