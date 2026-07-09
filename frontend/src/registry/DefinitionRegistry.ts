/**
 * DefinitionRegistry: lookup of metric, entity kind, relation type, line
 * category, table, capability, page, and graph lens definitions, with
 * fallback labels for unknown ids.
 */
import { fallbackLabel } from "./fallbackLabels";
import type { UiConfig } from "./uiConfigTypes";
import type { MetricDefinition } from "../domain/metric";
import type { EntityKindDefinition } from "../domain/entity";
import type { RelationTypeDefinition } from "../domain/relation";
import type { GraphLensDefinition } from "../domain/graph";
import type { TableDefinition } from "../domain/table";
import type { CapabilityDefinition, PageDefinition } from "../domain";

type Labeled = { id: string; label: string };
type LineCategoryDefinition = { id: string; label: string; defaultVisible: boolean; order: number };

export class DefinitionRegistry {
  private readonly metrics = new Map<string, MetricDefinition>();
  private readonly entityKinds = new Map<string, EntityKindDefinition>();
  private readonly relationTypes = new Map<string, RelationTypeDefinition>();
  private readonly lineCategories = new Map<string, LineCategoryDefinition>();
  private readonly tables = new Map<string, TableDefinition>();
  private readonly capabilities = new Map<string, CapabilityDefinition>();
  private readonly pages = new Map<string, PageDefinition>();
  private readonly graphLenses = new Map<string, GraphLensDefinition>();

  constructor(config: UiConfig) {
    for (const m of config.metrics) this.metrics.set(m.id, m);
    for (const k of config.entityKinds) this.entityKinds.set(k.id, k);
    for (const r of config.relationTypes) this.relationTypes.set(r.id, r);
    for (const c of config.lineCategories) this.lineCategories.set(c.id, c);
    for (const t of config.tables) this.tables.set(t.id, t);
    for (const c of config.capabilities) this.capabilities.set(c.id, c);
    for (const p of config.pages) this.pages.set(p.id, p);
    for (const l of config.graphLenses) this.graphLenses.set(l.id, l);
  }

  getMetric(id: string): MetricDefinition | null { return this.metrics.get(id) ?? null; }
  getEntityKind(id: string): EntityKindDefinition | null { return this.entityKinds.get(id) ?? null; }
  getRelationType(id: string): RelationTypeDefinition | null { return this.relationTypes.get(id) ?? null; }
  getLineCategory(id: string): LineCategoryDefinition | null { return this.lineCategories.get(id) ?? null; }
  getTable(id: string): TableDefinition | null { return this.tables.get(id) ?? null; }
  getCapability(id: string): CapabilityDefinition | null { return this.capabilities.get(id) ?? null; }
  getPage(id: string): PageDefinition | null { return this.pages.get(id) ?? null; }
  getGraphLens(id: string): GraphLensDefinition | null { return this.graphLenses.get(id) ?? null; }

  metricLabel(id: string): string { return labelOf(this.metrics, id); }
  entityKindLabel(id: string): string { return labelOf(this.entityKinds, id); }
  relationTypeLabel(id: string): string { return labelOf(this.relationTypes, id); }
  lineCategoryLabel(id: string): string { return labelOf(this.lineCategories, id); }
  tableLabel(id: string): string { return labelOf(this.tables, id); }
  graphLensLabel(id: string): string { return labelOf(this.graphLenses, id); }

  isCapabilityEnabled(id: string): boolean {
    return this.capabilities.get(id)?.enabled ?? false;
  }
}

function labelOf<T extends Labeled>(map: Map<string, T>, id: string): string {
  return map.get(id)?.label ?? fallbackLabel(id);
}
