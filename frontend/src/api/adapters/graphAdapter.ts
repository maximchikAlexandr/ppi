/**
 * Adapter: /api/v1/graph DTO -> generic EntityGraphModel.
 */
import type { EntityGraphModel } from "../../domain/graph";

type NodeDto = {
  entity?: { id?: string; kind?: string; label?: string };
  metrics?: { metricId?: string; value?: number | string | boolean | null; aggregation?: string | null }[];
  lineCounts?: Record<string, number>;
  distributions?: unknown[];
  attributes?: Record<string, unknown>;
};

type EdgeDto = {
  id?: string;
  source?: { id?: string; kind?: string; label?: string };
  target?: { id?: string; kind?: string; label?: string };
  relationTypeId?: string;
  metrics?: { metricId?: string; value?: number | string | boolean | null; aggregation?: string | null }[];
  contributions?: { typeId?: string; metricId?: string; value?: number }[];
  attributes?: Record<string, unknown>;
};

type Dto = {
  commitId?: string;
  lensId?: string;
  nodes?: NodeDto[];
  edges?: EdgeDto[];
};

export function adaptGraph(dto: Dto): EntityGraphModel {
  return {
    commitId: dto.commitId ?? "",
    lensId: dto.lensId ?? "default",
    nodes: (dto.nodes ?? []).map((n) => ({
      entity: {
        id: n.entity?.id ?? "",
        kind: n.entity?.kind ?? "unknown",
        label: n.entity?.label ?? n.entity?.id ?? "—",
      },
      metrics: (n.metrics ?? []).map((m) => ({
        metricId: m.metricId ?? "unknown",
        value: m.value ?? null,
        aggregation: m.aggregation ?? null,
      })),
      distributions: n.distributions as never,
      attributes: n.attributes,
      lineCounts: n.lineCounts ?? {},
    })),
    edges: (dto.edges ?? []).map((e) => ({
      id: e.id ?? `${e.source?.id}->${e.target?.id}`,
      source: {
        id: e.source?.id ?? "",
        kind: e.source?.kind ?? "unknown",
        label: e.source?.label ?? e.source?.id ?? "—",
      },
      target: {
        id: e.target?.id ?? "",
        kind: e.target?.kind ?? "unknown",
        label: e.target?.label ?? e.target?.id ?? "—",
      },
      relationTypeId: e.relationTypeId ?? "unknown",
      metrics: (e.metrics ?? []).map((m) => ({
        metricId: m.metricId ?? "unknown",
        value: m.value ?? null,
        aggregation: m.aggregation ?? null,
      })),
      contributions: (e.contributions ?? []).map((c) => ({
        typeId: c.typeId ?? "unknown",
        metricId: c.metricId ?? "unknown",
        value: c.value ?? 0,
      })),
      attributes: e.attributes,
    })),
  };
}