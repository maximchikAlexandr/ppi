/**
 * Generic graph tooltip builder. Uses metric and relation definitions
 * resolved through DefinitionRegistry, with fallback labels.
 */
import type { DefinitionRegistry } from "../../../registry/DefinitionRegistry";
import { fallbackLabel } from "../../../registry/fallbackLabels";
import type { EntityGraphEdge, EntityGraphNode } from "../../../domain/graph";

export function buildNodeTooltip(
  node: EntityGraphNode,
  registry: DefinitionRegistry,
): string {
  const label = registry.entityKindLabel(node.entity.kind);
  const metrics = node.metrics
    .map((m) => `${registry.metricLabel(m.metricId)}=${m.value ?? "—"}`)
    .join("\n");
  return `${label}: ${node.entity.label}\n${metrics || "(no metrics)"}`;
}

export function buildEdgeTooltip(
  edge: EntityGraphEdge,
  registry: DefinitionRegistry,
): string {
  const relLabel = registry.relationTypeLabel(edge.relationTypeId);
  const metrics = edge.metrics
    .map((m) => `${registry.metricLabel(m.metricId)}=${m.value ?? "—"}`)
    .join("\n");
  return `${edge.source.label} → ${edge.target.label}\n${relLabel}\n${metrics || "(no metrics)"}`;
}

export function fallbackRelationLabel(id: string): string {
  return fallbackLabel(id);
}
