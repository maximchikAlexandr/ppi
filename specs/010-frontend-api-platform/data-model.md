# Data Model: Frontend Platform and Public API Contract Foundation

**Feature**: `010-frontend-api-platform`  
**Status**: completed

This file defines the canonical model for the implementation plan. Use these names consistently in backend DTOs, frontend domain models, adapters, tests, and task descriptions.

## 1. Naming Rules

- Public `/api/v1` JSON fields: `camelCase`.
- Python internal fields: `snake_case` allowed.
- Frontend domain fields: `camelCase`.
- Public identifiers: strings.
- ID fields end with `Id` in public JSON and frontend domain.
- Do not expose `module_name`, `python_file_count`, `cyclomatic`, `cognitive`, `jones`, `manifest_depends`, `model_reuse`, `field_property`, or `python_lines` as required generic model fields.

## 2. Identifier Types

### EntityKindId

```ts
type EntityKindId = string;
```

Examples: `odoo.module`, `python.file`, `python.package`, `odoo.model`.

### EntityId

```ts
type EntityId = string;
```

Must be stable inside one project and one analysis store.

### MetricId

```ts
type MetricId = string;
```

Examples are backend/plugin-defined. Generic frontend code must not branch on concrete metric ids.

### RelationTypeId

```ts
type RelationTypeId = string;
```

Examples are backend/plugin-defined. Generic frontend code must use definitions and fallback labels.

### TableId

```ts
type TableId = string;
```

Examples: `entities.modules`, `entities.files`, `relations.current`.

### GraphLensId

```ts
type GraphLensId = string;
```

Examples: `module-dependencies`, `file-dependencies`, `model-relations`.

## 3. UI Configuration

### UiConfig

```ts
type UiConfig = {
  schemaVersion: number;
  profile: ProfileDefinition;
  plugins: PluginContributionDefinition[];
  capabilities: CapabilityDefinition[];
  pages: PageDefinition[];
  entityKinds: EntityKindDefinition[];
  metrics: MetricDefinition[];
  relationTypes: RelationTypeDefinition[];
  lineCategories: LineCategoryDefinition[];
  visualEncodings: VisualEncodingDefinition[];
  graphLenses: GraphLensDefinition[];
  tables: TableDefinition[];
  queries: QueryDefinition[];
};
```

Validation rules:

- `schemaVersion` is required.
- Every referenced metric id must exist in `metrics`.
- Every referenced entity kind id must exist in `entityKinds`.
- Every referenced relation type id must exist in `relationTypes` unless it is intentionally plugin-late-bound; missing labels must use fallback.
- Frontend must not render generic Graph, Tables, or Metrics Dashboard until UiConfig is loaded.

## 4. Profile and Plugin Definitions

### ProfileDefinition

```ts
type ProfileDefinition = {
  id: string;
  label: string;
  pluginIds: string[];
};
```

### PluginContributionDefinition

```ts
type PluginContributionDefinition = {
  pluginId: string;
  label: string;
  contributes: {
    entityKinds: EntityKindId[];
    metrics: MetricId[];
    relationTypes: RelationTypeId[];
    tables: TableId[];
    graphLenses: GraphLensId[];
    queries: string[];
    visualEncodings: string[];
  };
};
```

## 5. Capabilities and Pages

### CapabilityDefinition

```ts
type CapabilityDefinition = {
  id: string;
  label: string;
  enabled: boolean;
  reason?: string | null;
};
```

Required initial capability ids:

- `graph`
- `tables`
- `metricsDashboard`
- `diagnostics`

### PageDefinition

```ts
type PageDefinition = {
  id: string;
  label: string;
  kind: "snapshot" | "dashboard" | "tables" | "diagnostics" | "custom";
  requiredCapabilities: string[];
  defaultVisible: boolean;
};
```

## 6. Entity Model

### EntityKindDefinition

```ts
type EntityKindDefinition = {
  id: EntityKindId;
  label: string;
  pluralLabel: string;
  description?: string | null;
  icon?: string | null;
  defaultTableId?: TableId | null;
  supportedViews: string[];
};
```

### EntityRef

```ts
type EntityRef = {
  id: EntityId;
  kind: EntityKindId;
  label: string;
  path?: string | null;
  pluginId?: string | null;
};
```

Rules:

- `id`, `kind`, and `label` are mandatory.
- `moduleName` is not part of the generic model. If needed, it is an attribute or legacy adapter input.

### EntityTarget

```ts
type EntityTarget = EntityRef & {
  selectable: boolean;
  reason?: string | null;
};
```

Used by dashboard target selectors.

## 7. Metric Model

### MetricDefinition

```ts
type MetricDefinition = {
  id: MetricId;
  label: string;
  description?: string | null;
  valueType: "number" | "integer" | "ratio" | "duration" | "string" | "boolean";
  unit?: string | null;
  scope: "entity" | "relation" | "graph" | "table" | "project" | string;
  entityKinds: EntityKindId[];
  supportedAggregations: string[];
  defaultAggregation?: string | null;
  supportedViews: string[];
  higherIsWorse?: boolean | null;
  format?: ValueFormat | null;
  pluginId?: string | null;
};
```

### MetricValue

```ts
type MetricValue = {
  metricId: MetricId;
  value: number | string | boolean | null;
  aggregation?: string | null;
};
```

### MetricDistribution

```ts
type MetricDistribution = {
  metricId: MetricId;
  values: {
    count?: number;
    mean?: number;
    median?: number;
    p95?: number;
    max?: number;
  };
};
```

## 8. Value Format

```ts
type ValueFormat = {
  kind: "integer" | "decimal" | "compact" | "percent" | "datetime" | "text";
  precision?: number | null;
};
```

Rules:

- Formatting is determined by metric or column metadata.
- Generic renderers must not hardcode concrete metric ids.

## 9. Relation Model

### RelationTypeDefinition

```ts
type RelationTypeDefinition = {
  id: RelationTypeId;
  label: string;
  description?: string | null;
  group?: string | null;
  defaultVisible: boolean;
  pluginId?: string | null;
};
```

### RelationRecord

```ts
type RelationRecord = {
  id: string;
  source: EntityRef;
  target: EntityRef;
  relationTypeId: RelationTypeId;
  metrics: MetricValue[];
  attributes?: Record<string, unknown>;
};
```

### RelationContribution

```ts
type RelationContribution = {
  typeId: string;
  metricId: MetricId;
  value: number;
};
```

Rules:

- Relation type, metrics, and contributions are separate concepts.
- No fixed edge breakdown categories are allowed in generic models.

## 10. Graph Model

### GraphLensDefinition

```ts
type GraphLensDefinition = {
  id: GraphLensId;
  label: string;
  description?: string | null;
  nodeKinds: EntityKindId[];
  relationTypes: RelationTypeId[];
  defaultVisualEncoding: GraphVisualEncodingConfig;
};
```

### GraphVisualEncodingConfig

```ts
type GraphVisualEncodingConfig = {
  nodeSizeEncodingId?: string | null;
  nodeColorEncodingId?: string | null;
  edgeThicknessEncodingId?: string | null;
  nodeBadgeEncodingIds?: string[];
};
```

### GraphProjection

```ts
type GraphProjection = {
  commitId: string;
  lensId: GraphLensId;
  nodes: EntityGraphNode[];
  edges: EntityGraphEdge[];
};
```

### EntityGraphNode

```ts
type EntityGraphNode = {
  entity: EntityRef;
  metrics: MetricValue[];
  distributions?: MetricDistribution[];
  attributes?: Record<string, unknown>;
  lineCounts?: Record<string, number>;
};
```

### EntityGraphEdge

```ts
type EntityGraphEdge = {
  id: string;
  source: EntityRef;
  target: EntityRef;
  relationTypeId: RelationTypeId;
  metrics: MetricValue[];
  contributions?: RelationContribution[];
  attributes?: Record<string, unknown>;
};
```

## 11. Visual Encoding Model

```ts
type VisualEncodingDefinition = {
  id: string;
  label: string;
  appliesTo: "node" | "edge" | "table" | "dashboard";
  role: "size" | "color" | "brightness" | "thickness" | "badge" | "label";
  metricId?: MetricId | null;
  attributeId?: string | null;
  defaultSelected: boolean;
};
```

Rules:

- Graph settings render from these definitions.
- Unknown visual roles are ignored with a development warning.

## 12. Line Category Model

```ts
type LineCategoryDefinition = {
  id: string;
  label: string;
  defaultVisible: boolean;
  order: number;
};
```

Rules:

- Line count values may be stored in `lineCounts`.
- Tables must expose line counts as explicit columns.

## 13. Table Model

### TableDefinition

```ts
type TableDefinition = {
  id: TableId;
  label: string;
  description?: string | null;
  entityKindId?: EntityKindId | null;
  supportedActions: string[];
  defaultSort?: TableSort | null;
};
```

### TableProjection

```ts
type TableProjection = {
  tableId: TableId;
  title: string;
  commitId?: string | null;
  columns: TableColumnDefinition[];
  rows: TableRow[];
};
```

### TableColumnDefinition

```ts
type TableColumnDefinition = {
  id: string;
  label: string;
  valueType: "string" | "number" | "integer" | "boolean" | "date" | "datetime" | "metric" | "entity" | "json";
  metricId?: MetricId | null;
  format?: ValueFormat | null;
  sortable: boolean;
  visibleByDefault: boolean;
  align?: "left" | "right" | "center";
  width?: number | null;
};
```

### TableRow

```ts
type TableRow = {
  id: string;
  cells: Record<string, unknown>;
  actions?: TableRowAction[];
};
```

### TableRowAction

```ts
type TableRowAction = {
  id: string;
  label: string;
  kind: "drilldown" | "navigate" | "select";
  targetTableId?: TableId | null;
  params?: Record<string, unknown>;
};
```

### DrilldownFrame

```ts
type DrilldownFrame = {
  tableId: TableId;
  title: string;
  params: Record<string, unknown>;
};
```

## 14. Query Model

### QueryDefinition

```ts
type QueryDefinition = {
  id: string;
  label: string;
  resultKind: "timeseries" | "ranking" | "distribution";
  parameters: QueryParameterDefinition[];
};
```

### QueryParameterDefinition

```ts
type QueryParameterDefinition = {
  id: string;
  label: string;
  kind: "entityKind" | "target" | "metric" | "aggregation" | "number" | "select";
  required: boolean;
};
```

### MetricQueryState

```ts
type MetricQueryState = {
  entityKindId: EntityKindId;
  targetId?: EntityId | null;
  metricId: MetricId;
  aggregation: string;
};
```

State rules:

- When `entityKindId` changes, recompute valid targets and metrics.
- When `metricId` changes, recompute valid aggregations.
- Do not send requests while state is invalid.
- If no valid state exists, show unavailable state.

## 15. Error Model

```ts
type ErrorResponse = {
  error: {
    code: string;
    message: string;
    details?: unknown;
    requestId?: string | null;
  };
};
```

Rules:

- All `/api/v1` errors use this shape.
- Public OpenAPI documents this schema.
- Frontend adapters convert it to frontend domain errors.

## 16. State Transitions

### API Stability

```text
experimental
  -> baseline_ready
  -> stable
```

Transition rules:

- `experimental`: `/api/v1` exists, diff reporting is non-blocking.
- `baseline_ready`: Graph, Tables, and Metrics Dashboard have migrated to generated transport plus adapters.
- `stable`: baseline artifact is saved, breaking-change detection becomes blocking.

### Frontend Page Migration

```text
legacy
  -> adapted_legacy
  -> public_v1_adapter
  -> generic_component
```

Rules:

- `legacy`: page uses old `/api/*` client directly.
- `adapted_legacy`: page uses `frontend/src/legacy/**` adapter.
- `public_v1_adapter`: page uses `/api/v1` generated transport through adapter.
- `generic_component`: page renders only domain/view models.

## 17. Strict Schema Clarifications for Implementers

### 17.1 Required vs optional response fields

Unless explicitly marked optional with `?`, fields in the TypeScript-like models are required in `/api/v1` responses. Required array fields must be present as empty arrays when empty. Required object fields must be present as empty objects when empty.

### 17.2 Id stability

- `EntityId`, `MetricId`, `RelationTypeId`, `TableId`, and `GraphLensId` are opaque strings for the frontend.
- The frontend must compare ids only by exact string equality.
- The frontend must not parse ids to infer backend type, module name, file path, or plugin.

### 17.3 Table cell contract

For each `TableRow`, every key in `cells` should correspond to a `TableColumnDefinition.id`. Extra keys may be preserved for diagnostics but generic table rendering must ignore extras by default.

### 17.4 Row action contract

`TableRowAction.params` is passed back to `GET /api/v1/tables/{tableId}` as query parameters only when the receiving table definition documents those parameters through a `QueryDefinition` or table-specific metadata. Implementers must not infer `module_name` or file-specific parameter names.

### 17.5 Error details contract

`ErrorResponse.error.details` may be any JSON value, but public clients must rely only on `code`, `message`, and `requestId` for control flow. `details` is diagnostic and not stable before the baseline.

### 17.6 Time and ordering contract

- `authoredAt` uses ISO 8601 UTC strings.
- `commitOrder` is a unique integer assigned at commit ingestion, monotonically increasing in repository history order. Ties are not expected; if two records share `commitOrder`, the one with the lexicographically greater `commitId` is the tie-breaker (defensive only).
- When a latest commit is needed, choose the greatest `commitOrder`, not lexicographic `commitId` order.
- If the requested commit is absent from the store, read endpoints return `ErrorResponse` with code `STORE_NOT_READY` (see §15).

### 17.7 Dashboard normalization result

Implement `MetricQueryStateResult` explicitly:

```ts
type MetricQueryStateResult =
  | { status: "valid"; state: MetricQueryState }
  | { status: "unavailable"; reason: string };
```

Generic Dashboard code may send metric requests only when `status === "valid"`.
