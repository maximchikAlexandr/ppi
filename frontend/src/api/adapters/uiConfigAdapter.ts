/**
 * Adapter: /api/v1/ui/config DTO -> generic UiConfig domain model.
 *
 * The adapter is the only place that may import the generated DTO shape.
 * Every field is normalized field-by-field (no `as` casts over whole
 * objects): a missing required field becomes a visible default, never
 * an undefined typed as present.
 */
import type { UiConfig } from "../../registry/uiConfigTypes";
import type { MetricDefinition, ValueFormat } from "../../domain/metric";
import type { EntityKindDefinition } from "../../domain/entity";
import type { RelationTypeDefinition } from "../../domain/relation";
import type {
  GraphVisualEncodingConfig,
} from "../../domain/graph";
import type { VisualEncodingDefinition } from "../../domain/visualEncoding";
import type { TableDefinition } from "../../domain/table";
import type { QueryDefinition } from "../../domain/query";
import type {
  PageDefinition,
} from "../../domain";

type Dto = {
  schemaVersion?: number;
  profile?: { id?: string; label?: string; pluginIds?: string[] };
  plugins?: unknown[];
  capabilities?: { id?: string; label?: string; enabled?: boolean; reason?: string | null }[];
  pages?: { id?: string; label?: string; kind?: string; requiredCapabilities?: string[]; defaultVisible?: boolean }[];
  entityKinds?: Partial<EntityKindDefinition>[];
  metrics?: Partial<MetricDefinition>[];
  relationTypes?: Partial<RelationTypeDefinition>[];
  lineCategories?: { id?: string; label?: string; defaultVisible?: boolean; order?: number }[];
  visualEncodings?: Partial<VisualEncodingDefinition>[];
  graphLenses?: { id?: string; label?: string; description?: string | null; nodeKinds?: string[]; relationTypes?: string[]; defaultVisualEncoding?: GraphVisualEncodingConfig }[];
  tables?: Partial<TableDefinition>[];
  queries?: Partial<QueryDefinition>[];
};

export function adaptUiConfig(dto: Dto): UiConfig {
  return {
    schemaVersion: dto.schemaVersion ?? 1,
    profile: {
      id: dto.profile?.id ?? "default",
      label: dto.profile?.label ?? "Default",
      pluginIds: dto.profile?.pluginIds ?? [],
    },
    plugins: normalizePlugins(dto.plugins ?? []),
    capabilities: (dto.capabilities ?? []).map((c) => ({
      id: c.id ?? "unknown",
      label: c.label ?? c.id ?? "Unknown",
      enabled: c.enabled ?? false,
      reason: c.reason ?? null,
    })),
    pages: (dto.pages ?? []).map((p) => ({
      id: p.id ?? "unknown",
      label: p.label ?? p.id ?? "Unknown",
      kind: (p.kind as PageDefinition["kind"]) ?? "custom",
      requiredCapabilities: p.requiredCapabilities ?? [],
      defaultVisible: p.defaultVisible ?? true,
    })),
    entityKinds: (dto.entityKinds ?? []).map((k) => ({
      id: k.id ?? "unknown",
      label: k.label ?? k.id ?? "Unknown",
      pluralLabel: k.pluralLabel ?? k.label ?? k.id ?? "Unknown",
      description: k.description ?? null,
      icon: k.icon ?? null,
      defaultTableId: k.defaultTableId ?? null,
      supportedViews: k.supportedViews ?? [],
    })),
    metrics: (dto.metrics ?? []).map((m) => ({
      id: m.id ?? "unknown",
      label: m.label ?? m.id ?? "Unknown",
      description: m.description ?? null,
      valueType: m.valueType ?? "number",
      unit: m.unit ?? null,
      scope: m.scope ?? "entity",
      entityKinds: m.entityKinds ?? [],
      supportedAggregations: m.supportedAggregations ?? [],
      defaultAggregation: m.defaultAggregation ?? null,
      supportedViews: m.supportedViews ?? [],
      higherIsWorse: m.higherIsWorse ?? null,
      format: normalizeFormat(m.format),
      pluginId: m.pluginId ?? null,
    })),
    relationTypes: (dto.relationTypes ?? []).map((r) => ({
      id: r.id ?? "unknown",
      label: r.label ?? r.id ?? "Unknown",
      description: r.description ?? null,
      group: r.group ?? null,
      defaultVisible: r.defaultVisible ?? false,
      pluginId: r.pluginId ?? null,
    })),
    lineCategories: (dto.lineCategories ?? []).map((c) => ({
      id: c.id ?? "unknown",
      label: c.label ?? c.id ?? "Unknown",
      defaultVisible: c.defaultVisible ?? false,
      order: c.order ?? 0,
    })),
    visualEncodings: (dto.visualEncodings ?? []).map((e) => ({
      id: e.id ?? "unknown",
      label: e.label ?? e.id ?? "Unknown",
      appliesTo: e.appliesTo ?? "node",
      role: e.role ?? "size",
      metricId: e.metricId ?? null,
      attributeId: e.attributeId ?? null,
      defaultSelected: e.defaultSelected ?? false,
    })),
    graphLenses: (dto.graphLenses ?? []).map((l) => ({
      id: l.id ?? "unknown",
      label: l.label ?? l.id ?? "Unknown",
      description: l.description ?? null,
      nodeKinds: l.nodeKinds ?? [],
      relationTypes: l.relationTypes ?? [],
      defaultVisualEncoding: l.defaultVisualEncoding ?? {},
    })),
    tables: (dto.tables ?? []).map((t) => ({
      id: t.id ?? "unknown",
      label: t.label ?? t.id ?? "Unknown",
      description: t.description ?? null,
      entityKindId: t.entityKindId ?? null,
      supportedActions: t.supportedActions ?? [],
      defaultSort: t.defaultSort ?? null,
    })),
    queries: (dto.queries ?? []).map((q) => ({
      id: q.id ?? "unknown",
      label: q.label ?? q.id ?? "Unknown",
      resultKind: normalizeResultKind(q.resultKind),
      parameters: q.parameters ?? [],
    })),
  };
}

const KNOWN_RESULT_KINDS: ReadonlySet<QueryDefinition["resultKind"]> = new Set([
  "timeseries",
  "ranking",
  "distribution",
]);

function normalizeResultKind(kind: string | undefined): QueryDefinition["resultKind"] {
  if (kind && (KNOWN_RESULT_KINDS as ReadonlySet<string>).has(kind)) {
    return kind as QueryDefinition["resultKind"];
  }
  // Unknown kind: fall back to "timeseries" so a future backend
  // kind never silently breaks the dashboard. The first metric
  // a page renders is always a timeseries; this is the safest
  // no-op until the page handles the new kind explicitly.
  return "timeseries";
}

function normalizeFormat(f: Partial<ValueFormat> | null | undefined): ValueFormat | null {
  if (f == null || f.kind == null) return null;
  return { kind: f.kind, precision: (f as { precision?: number | null }).precision ?? null };
}

function normalizePlugins(plugins: unknown[]): UiConfig["plugins"] {
  if (!Array.isArray(plugins)) return [];
  return plugins
    .filter((p): p is { pluginId?: string; label?: string; contributes?: Record<string, unknown> } =>
      typeof p === "object" && p !== null)
    .map((p) => ({
      pluginId: p.pluginId ?? "unknown",
      label: p.label ?? p.pluginId ?? "Unknown",
      contributes: {
        entityKinds: arrayOrEmpty(p.contributes?.entityKinds),
        metrics: arrayOrEmpty(p.contributes?.metrics),
        relationTypes: arrayOrEmpty(p.contributes?.relationTypes),
        tables: arrayOrEmpty(p.contributes?.tables),
        graphLenses: arrayOrEmpty(p.contributes?.graphLenses),
        queries: arrayOrEmpty(p.contributes?.queries),
        visualEncodings: arrayOrEmpty(p.contributes?.visualEncodings),
      },
    }));
}

function arrayOrEmpty(v: unknown): string[] {
  return Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : [];
}