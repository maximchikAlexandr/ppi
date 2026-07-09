import type { EntityKindId, MetricId } from "../domain/ids";
import type { MetricDefinition } from "../domain/metric";

export type GenericMetricQueryState = {
  entityKindId: EntityKindId;
  targetId?: string | null;
  metricId: MetricId;
  aggregation: string;
};

export function getValidMetricsForEntityKind(
  metrics: readonly MetricDefinition[],
  entityKindId: EntityKindId,
): readonly MetricDefinition[] {
  return metrics.filter((m) => m.entityKinds.includes(entityKindId));
}

export function getValidAggregationsForMetric(
  metric: MetricDefinition | null,
): readonly string[] {
  if (!metric) return [];
  return metric.supportedAggregations;
}

export function normalizeMetricQueryState(args: {
  entityKindId: EntityKindId | null;
  targetId: string | null;
  metricId: MetricId | null;
  aggregation: string | null;
  metrics: readonly MetricDefinition[];
}): GenericMetricQueryState | null {
  const entityKindId = args.entityKindId;
  if (!entityKindId) return null;
  const validMetrics = getValidMetricsForEntityKind(args.metrics, entityKindId);
  if (!validMetrics.length) return null;
  const metric = validMetrics.find((m) => m.id === args.metricId) ?? validMetrics[0];
  const aggregations = getValidAggregationsForMetric(metric);
  const aggregation = aggregations.includes(args.aggregation ?? "")
    ? (args.aggregation as string)
    : (metric.defaultAggregation ?? aggregations[0] ?? "mean");
  return {
    entityKindId,
    targetId: args.targetId,
    metricId: metric.id,
    aggregation,
  };
}
