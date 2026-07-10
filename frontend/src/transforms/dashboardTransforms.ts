import type { EntityKindId, MetricId } from "../domain/ids";
import type { MetricDefinition } from "../domain/metric";
import type { MetricQueryStateResult } from "../domain/query";

export type { MetricQueryStateResult } from "../domain/query";

export type MetricQueryUnavailableReason =
  | "missing_entity_kind"
  | "no_metrics_for_entity_kind"
  | "missing_aggregation"
  | "unknown_aggregation"
  | "missing_target";

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

/**
 * Pure validation: turns a partial metric query state into a fully
 * validated state or an explicit unavailable reason. The Dashboard
 * never fires a request when this returns `unavailable`.
 */
export function normalizeMetricQueryState(args: {
  entityKindId: EntityKindId | null;
  targetId: string | null;
  metricId: MetricId | null;
  aggregation: string | null;
  metrics: readonly MetricDefinition[];
  availableTargetIds?: ReadonlySet<string>;
}): MetricQueryStateResult {
  if (!args.entityKindId) {
    return { status: "unavailable", reason: "missing_entity_kind" };
  }
  const validMetrics = getValidMetricsForEntityKind(args.metrics, args.entityKindId);
  if (validMetrics.length === 0) {
    return { status: "unavailable", reason: "no_metrics_for_entity_kind" };
  }
  const metric = args.metricId
    ? validMetrics.find((m) => m.id === args.metricId) ?? validMetrics[0]!
    : validMetrics[0]!;
  const aggregations = getValidAggregationsForMetric(metric);
  if (aggregations.length === 0) {
    return { status: "unavailable", reason: "missing_aggregation" };
  }
  const requested = args.aggregation ?? metric.defaultAggregation ?? aggregations[0]!;
  if (!aggregations.includes(requested)) {
    return { status: "unavailable", reason: "unknown_aggregation" };
  }
  if (
    args.availableTargetIds &&
    args.targetId !== null &&
    !args.availableTargetIds.has(args.targetId)
  ) {
    return { status: "unavailable", reason: "missing_target" };
  }
  return {
    status: "valid",
    state: {
      entityKindId: args.entityKindId,
      targetId: args.targetId,
      metricId: metric.id,
      aggregation: requested,
    },
  };
}
