# Contract: Frontend Platform Boundaries

**Feature**: `010-frontend-api-platform`  
**Status**: Hardened draft; implementation not yet complete

## 1. Import Rules

### Generic code MAY import

```text
frontend/src/domain/**
frontend/src/registry/**
frontend/src/api/publicApi.ts
frontend/src/api/adapters/**
frontend/src/components/generic/**
frontend/src/visualization/**
```

### Generic code MUST NOT import

```text
frontend/src/api/generated/**
frontend/src/legacy/**
frontend/src/registry/odooProfile.ts
```

### Pages MUST NOT read legacy fields directly

Pages and generic components MUST NOT read these fields outside `frontend/src/legacy/**`:

```text
module_name
python_file_count
cyclomatic
cognitive
jones
manifest_depends
model_reuse
field_property
extension_or_method
python_lines
xml_lines
score_in
score_out
```

## 2. Required Frontend Modules

Create these modules exactly.

```text
frontend/src/domain/ids.ts
frontend/src/domain/metric.ts
frontend/src/domain/entity.ts
frontend/src/domain/relation.ts
frontend/src/domain/graph.ts
frontend/src/domain/table.ts
frontend/src/domain/filter.ts
frontend/src/domain/action.ts
frontend/src/domain/visualEncoding.ts
frontend/src/domain/capability.ts
frontend/src/domain/page.ts
```

Each module exports only frontend domain types and pure helpers. No module in `domain/` may import React, generated API DTOs, legacy DTOs, or Mantine.

## 3. Definition Registry Contract

`frontend/src/registry/DefinitionRegistry.ts` MUST export:

```ts
export class DefinitionRegistry {
  metric(id: string): MetricDefinition | undefined;
  entityKind(id: string): EntityKindDefinition | undefined;
  relationType(id: string): RelationTypeDefinition | undefined;
  lineCategory(id: string): LineCategoryDefinition | undefined;
  table(id: string): TableDefinition | undefined;
  visualEncoding(id: string): VisualEncodingDefinition | undefined;
  page(id: string): PageDefinition | undefined;
  capability(id: string): CapabilityDefinition | undefined;
  labelForUnknown(id: string): string;
  labelForMetric(id: string): string;
  labelForRelationType(id: string): string;
  formatMetricValue(metricId: string, value: unknown): string;
}
```

## 4. UiConfigProvider Contract

`frontend/src/registry/UiConfigProvider.tsx` MUST provide:

```ts
export function UiConfigProvider(props: { children: React.ReactNode }): JSX.Element;
export function useUiConfig(): UiConfig;
export function useDefinitionRegistry(): DefinitionRegistry;
```

Rules:

- While config is loading, generic pages show a loading state.
- If config fails to load, generic pages show a blocking unavailable state.
- Generic pages MUST NOT fallback to hardcoded Odoo/Python defaults.

## 5. Public API Facade Contract

`frontend/src/api/publicApi.ts` MUST be the only generic API entrypoint.

It MUST export:

```ts
export const publicApi: {
  getStatus(): Promise<Status>;
  getUiConfig(): Promise<UiConfig>;
  listCommits(): Promise<CommitList>;
  listEntities(params: ListEntitiesParams): Promise<EntityTargetList>;
  getGraph(params: GetGraphParams): Promise<GraphProjection>;
  listTables(): Promise<TableDefinitionList>;
  getTable(params: GetTableParams): Promise<TableProjection>;
  getMetricTimeseries(params: MetricTimeseriesParams): Promise<MetricTimeseries>;
  getMetricHotspots(params: MetricHotspotsParams): Promise<MetricHotspots>;
};
```

Rules:

- `publicApi` returns frontend domain models, not generated DTOs.
- Generated DTO imports are allowed only inside `publicApi.ts` and `frontend/src/api/adapters/**`.

## 6. Adapter Contract

Adapters MUST be pure functions.

Required adapters:

```text
frontend/src/api/adapters/uiConfigAdapter.ts
frontend/src/api/adapters/entityAdapter.ts
frontend/src/api/adapters/graphAdapter.ts
frontend/src/api/adapters/tableAdapter.ts
frontend/src/api/adapters/dashboardAdapter.ts
frontend/src/api/adapters/errorAdapter.ts
```

Each adapter file MUST include tests.

Adapter rules:

- Accept generated DTOs.
- Return frontend domain models.
- Never return raw DTOs.
- Use `DefinitionRegistry` only when formatting/lookup is required.
- Preserve unknown ids and attach fallback-ready labels when required.

## 7. Generic Component Contract

Generic components receive domain/view models only.

Required components:

```text
frontend/src/components/generic/values/GenericValueRenderer.tsx
frontend/src/components/generic/table/GenericDataTable.tsx
frontend/src/components/generic/graph/EntityGraph.tsx
```

`GenericDataTable` props:

```ts
type GenericDataTableProps = {
  table: TableProjection;
  onAction: (row: TableRow, action: TableRowAction) => void;
};
```

`EntityGraph` props:

```ts
type EntityGraphProps = {
  graph: GraphProjection;
  visualConfig: GraphVisualEncodingConfig;
  selectedEntityId: string | null;
  onSelectEntity: (entityId: string | null) => void;
};
```

## 8. Dashboard State Contract

Dashboard query state normalization MUST be implemented as pure functions:

```ts
normalizeMetricQueryState(state, registry, availableTargets): MetricQueryStateResult;
getValidMetricsForEntityKind(entityKindId, registry): MetricDefinition[];
getValidAggregationsForMetric(metricId, registry): string[];
```

Rules:

- If current metric is invalid, replace it with first valid metric.
- If current aggregation is invalid, replace it with default aggregation or first valid aggregation.
- If no valid metric exists, do not send request.
- If targets are required and empty, do not send request.

## 9. Legacy Boundary Contract

`frontend/src/legacy/**` is the only place where old DTO field names are allowed.

Required files:

```text
frontend/src/legacy/legacyApiTypes.ts
frontend/src/legacy/legacyGraphAdapter.ts
frontend/src/legacy/legacyTableAdapter.ts
frontend/src/legacy/legacyDashboardAdapter.ts
frontend/src/legacy/legacyOdooLabels.ts
```

Legacy modules MUST NOT be imported from `frontend/src/components/generic/**`.

## 10. Boundary Scanner Requirements

`scripts/check_frontend_boundaries.py` MUST implement these checks:

1. Fail if forbidden identifiers appear in generic paths listed by `migration-boundaries.md`, excluding comments in the scanner itself.
2. Fail if `frontend/src/components/generic/**`, `frontend/src/domain/**`, or `frontend/src/registry/**` imports `frontend/src/api/generated/**`.
3. Fail if `frontend/src/components/generic/**`, `frontend/src/domain/**`, or `frontend/src/registry/**` imports `frontend/src/legacy/**`.
4. Allow generated DTO imports only in `frontend/src/api/publicApi.ts`, `frontend/src/api/internalApi.ts`, and `frontend/src/api/adapters/**`.
5. Print the file path, line number, and token/import that caused each violation.

The scanner must be deterministic and must exit with code `1` on violations and `0` on success.

## 11. Adapter Test Requirements

Each adapter test must include:

- one happy-path DTO fixture;
- one unknown id fixture proving fallback labels are preserved or generated;
- one missing optional-array fixture proving empty arrays are produced;
- one legacy-field leakage assertion proving forbidden fields do not appear in the returned domain model except inside `attributes` when intentionally preserved for diagnostics.
