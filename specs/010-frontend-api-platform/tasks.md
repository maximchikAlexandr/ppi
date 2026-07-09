# Tasks: Frontend Platform and Public API Contract Foundation

**Feature**: `010-frontend-api-platform`  
**Input artifacts**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/*.md`, `quickstart.md`  
**Implementation rule**: Follow the paths, endpoint names, field names, and tool choices exactly. Do not invent alternate endpoint names, alternate SDK tools, alternate casing, or alternate migration boundaries.

## Required task format validation

Every implementation task below uses this format:

```text
- [ ] T001 Description with file path
- [ ] T012 [P] Description with file path
- [ ] T034 [P] [US1] Description with file path
- [ ] T035 [US1] Description with file path
```

## Phase 1: Setup

- [X] T001 Add API governance dev dependencies `@stoplight/spectral-cli`, `@redocly/cli`, `openapi-typescript`, `openapi-fetch`, and `oasdiff` command wrappers in `frontend/package.json`
- [X] T002 Add root OpenAPI artifact directories with placeholder files in `openapi/baseline/README.md`
- [X] T003 Create API export script that imports the FastAPI app and writes OpenAPI JSON in `scripts/export_openapi.py`
- [X] T004 Create API check shell script that exports OpenAPI, runs Spectral, runs Redocly, and generates frontend types in `scripts/check_openapi.sh`
- [X] T005 Create non-blocking API diff shell script using `oasdiff changelog` in `scripts/diff_openapi.sh`
- [X] T006 Add Spectral rules requiring operationId, tags, summaries, `/api/v1` public paths, common error responses, and consistent request parameter naming across `/api/v1` endpoints in `.spectral.yaml`
- [X] T007 Add Redocly configuration for OpenAPI 3.1 validation and bundling in `redocly.yaml`
- [X] T008 Add generated API output directory placeholder in `frontend/src/api/generated/.gitkeep`
- [X] T009 Add frontend API generated artifacts to source-control policy with a clear comment in `frontend/.gitignore`
- [X] T010 Document the exact setup commands from `quickstart.md` in `docs/api-contract-workflow.md`

---

## Phase 2: Foundational Prerequisites

These tasks block all user stories. Complete them before starting story phases.

- [X] T011 Create the new API v1 router module and mount it under `/api/v1` from the FastAPI app in `src/ppi/server/api_v1.py`
- [X] T012 Add API v1 router registration without removing legacy routes in `src/ppi/server/api.py`
- [X] T013 Define a Pydantic base model that emits `camelCase` aliases while keeping Python fields in `snake_case` in `src/ppi/server/v1_schemas.py`
- [X] T014 Define the shared `ErrorResponse` and `ErrorBody` models with `code`, `message`, `details`, and `requestId` in `src/ppi/server/v1_schemas.py`
- [X] T015 Add an API v1 exception handler that converts validation and domain errors to `ErrorResponse` in `src/ppi/server/api_v1.py`
- [X] T016 Create backend projection module skeleton with explicit functions for UI config, entities, graph, tables, metrics, and hotspots in `src/ppi/query/projections.py`
- [X] T017 Create API v1 handler module skeleton that delegates to projection functions in `src/ppi/query/v1_handlers.py`
- [X] T018 Create frontend domain barrel exports for generic primitives in `frontend/src/domain/index.ts`
- [X] T019 Create the public API facade module that will be the only generic frontend import point for public transport calls in `frontend/src/api/publicApi.ts`
- [X] T020 Create the internal API facade module for generated internal/legacy access isolation in `frontend/src/api/internalApi.ts`
- [X] T021 Create legacy boundary directory and index file in `frontend/src/legacy/index.ts`
- [X] T022 Create the frontend adapter barrel file in `frontend/src/api/adapters/index.ts`
- [X] T023 Add a comment block defining forbidden domain identifiers for generic frontend code in `frontend/src/legacy/legacyApiTypes.ts`
- [X] T024 Add the generated-client import rule documentation in `frontend/src/api/README.md`
- [X] T025 Verify the project still starts with legacy endpoints after mounting `/api/v1` in `tests/server/test_api_v1_mount.py`

---

## Phase 3: User Story 1 - Generic frontend renders backend-provided domain metadata (Priority: P1)

**Goal**: Generic frontend components render metrics, entities, relation types, line categories, values, labels, and capabilities from definitions instead of hardcoded Python/Odoo fields.

**Independent Test**: Use a fixture with unknown metric, relation type, line category, and entity kind. The frontend renders fallback labels and generic values without component code changes or runtime crashes.

### Implementation tasks

- [X] T026 [P] [US1] Define `EntityKindId`, `EntityId`, `MetricId`, `RelationTypeId`, `TableId`, and `GraphLensId` string aliases in `frontend/src/domain/ids.ts`
- [X] T027 [P] [US1] Define `MetricDefinition`, `MetricValue`, `MetricDistribution`, and `ValueFormat` in `frontend/src/domain/metric.ts`
- [X] T028 [P] [US1] Define `EntityKindDefinition`, `EntityRef`, and `EntityTarget` in `frontend/src/domain/entity.ts`
- [X] T029 [P] [US1] Define `RelationTypeDefinition`, `RelationRecord`, and `RelationContribution` in `frontend/src/domain/relation.ts`
- [X] T030 [P] [US1] Define `CapabilityDefinition` and `PageDefinition` in `frontend/src/domain/capability.ts`
- [X] T031 [P] [US1] Define `FilterDefinition`, `FilterOption`, and `FilterValue` in `frontend/src/domain/filter.ts`
- [X] T032 [P] [US1] Define `ActionDefinition`, `TableRowAction`, and action parameter types in `frontend/src/domain/action.ts`
- [X] T033 [P] [US1] Define `UiConfig`, `ProfileDefinition`, and `PluginContributionDefinition` in `frontend/src/registry/uiConfigTypes.ts`
- [X] T034 [P] [US1] Implement deterministic fallback label conversion from identifiers to readable labels in `frontend/src/registry/fallbackLabels.ts`
- [X] T035 [US1] Implement `DefinitionRegistry` with lookup methods for metrics, entity kinds, relation types, line categories, tables, capabilities, pages, and fallbacks in `frontend/src/registry/DefinitionRegistry.ts`
- [X] T036 [US1] Implement `UiConfigProvider` that loads UI config before rendering generic views in `frontend/src/registry/UiConfigProvider.tsx`
- [X] T037 [US1] Wrap the app with `UiConfigProvider` without changing existing route names in `frontend/src/App.tsx`
- [X] T038 [P] [US1] Implement `GenericValueRenderer` that routes values by metadata value type in `frontend/src/components/generic/values/GenericValueRenderer.tsx`
- [X] T039 [P] [US1] Implement `MetricValueRenderer` using metric definition labels, units, and formats in `frontend/src/components/generic/values/MetricValueRenderer.tsx`
- [X] T040 [P] [US1] Implement `NumberValueRenderer` with integer, decimal, compact, and percent formatting in `frontend/src/components/generic/values/NumberValueRenderer.tsx`
- [X] T041 [P] [US1] Implement `DateValueRenderer` with ISO input support and local display in `frontend/src/components/generic/values/DateValueRenderer.tsx`
- [X] T042 [P] [US1] Implement `BooleanValueRenderer` with stable true/false/empty labels in `frontend/src/components/generic/values/BooleanValueRenderer.tsx`
- [X] T043 [US1] Add unknown-definition fixture for metric, relation type, line category, and entity kind in `frontend/src/registry/__fixtures__/unknownUiConfig.ts`
- [X] T044 [US1] Add tests for fallback labels and unknown identifiers in `frontend/src/registry/DefinitionRegistry.test.ts`
- [X] T045 [US1] Add tests for generic value rendering using unknown metric definitions in `frontend/src/components/generic/values/GenericValueRenderer.test.tsx`

---

## Phase 4: User Story 2 - Versioned API contract supports frontend migration and future public use (Priority: P1)

**Goal**: Add `/api/v1` generic endpoints with `camelCase` JSON, common errors, operationIds, response models, and exportable OpenAPI contract.

**Independent Test**: Export OpenAPI and verify `/api/v1` endpoints have stable operationIds, tags, summaries, `camelCase` fields, and common error responses.

### Implementation tasks

- [X] T046 [P] [US2] Define `StatusV1Response` with `projectId`, `branch`, `storePresent`, `writerActive`, `commitCount`, and `apiStatus` in `src/ppi/server/v1_schemas.py`
- [X] T047 [P] [US2] Define `CommitSummaryV1` and `ListCommitsV1Response` with `commitId`, `commitOrder`, `authoredAt`, and `summary` in `src/ppi/server/v1_schemas.py`
- [X] T048 [P] [US2] Define `UiConfigV1Response` and nested definition models from `data-model.md` in `src/ppi/server/v1_schemas.py`
- [X] T049 [P] [US2] Define `EntityRefV1`, `EntityTargetV1`, and `ListEntitiesV1Response` in `src/ppi/server/v1_schemas.py`
- [X] T050 [P] [US2] Define `GraphNodeV1`, `GraphEdgeV1`, `GraphV1Response`, and relation contribution models in `src/ppi/server/v1_schemas.py`
- [X] T051 [P] [US2] Define `TableColumnV1`, `TableRowV1`, `TableRowActionV1`, `TableV1Response`, and `ListTablesV1Response` in `src/ppi/server/v1_schemas.py`
- [X] T052 [P] [US2] Define `MetricTimeseriesV1Response`, `MetricHotspotsV1Response`, and query result point models in `src/ppi/server/v1_schemas.py`
- [X] T053 [US2] Implement `GET /api/v1/status` with operationId `getStatusV1` in `src/ppi/server/api_v1.py`
- [X] T054 [US2] Implement `GET /api/v1/ui/config` with operationId `getUiConfigV1` in `src/ppi/server/api_v1.py`
- [X] T055 [US2] Implement `GET /api/v1/commits` with operationId `listCommitsV1` in `src/ppi/server/api_v1.py`
- [X] T056 [US2] Implement `GET /api/v1/entities` with operationId `listEntitiesV1` and query parameters `entityKindId`, `commitId`, and `limit` in `src/ppi/server/api_v1.py`
- [X] T057 [US2] Implement `GET /api/v1/graph` with operationId `getGraphV1` and query parameters `lensId`, `commitId`, and `includeZeroWeight` in `src/ppi/server/api_v1.py`
- [X] T058 [US2] Implement `GET /api/v1/tables` with operationId `listTablesV1` in `src/ppi/server/api_v1.py`
- [X] T059 [US2] Implement `GET /api/v1/tables/{tableId}` with operationId `getTableV1` and query parameters `commitId` and `parentEntityId` in `src/ppi/server/api_v1.py`
- [X] T060 [US2] Implement `GET /api/v1/metrics/timeseries` with operationId `getMetricTimeseriesV1` in `src/ppi/server/api_v1.py`
- [X] T061 [US2] Implement `GET /api/v1/metrics/hotspots` with operationId `getMetricHotspotsV1` in `src/ppi/server/api_v1.py`
- [X] T062 [US2] Implement `build_ui_config_projection` using existing catalog values and explicit generic definitions in `src/ppi/query/projections.py`
- [X] T063 [US2] Implement `build_graph_projection` by adapting existing graph data into generic nodes, edges, metrics, and relation types in `src/ppi/query/projections.py`
- [X] T064 [US2] Implement `build_table_projection` by adapting module, file, and relation tables into generic columns, rows, and row actions in `src/ppi/query/projections.py`
- [X] T065 [US2] Implement `build_metric_query_projection` for timeseries and hotspots using generic metric ids and entity kind ids in `src/ppi/query/projections.py`
- [X] T066 [US2] Add tests that `/api/v1` responses use `camelCase` field names in `tests/server/test_api_v1_camel_case.py`
- [X] T067 [US2] Add tests that `/api/v1` errors use `ErrorResponse` instead of FastAPI default validation output in `tests/server/test_api_v1_errors.py`
- [X] T068 [US2] Add OpenAPI tests for required operationIds and tags in `tests/server/test_api_v1_openapi.py`

---

## Phase 5: User Story 3 - Frontend uses generated transport types but keeps its own domain model (Priority: P1)

**Goal**: Generate transport types/client from OpenAPI, isolate generated DTOs, and force all generic frontend data through explicit adapters.

**Independent Test**: Generic components do not import generated DTOs. API response changes fail generated transport/adapters first, not generic component contracts.

### Implementation tasks

- [X] T069 [US3] Add `openapi:export`, `openapi:types`, and `openapi:check` npm scripts in `frontend/package.json`
- [X] T070 [US3] Generate initial OpenAPI TypeScript types to `frontend/src/api/generated/schema.d.ts`
- [X] T071 [US3] Create `openapi-fetch` client factory with base URL configuration in `frontend/src/api/http.ts`
- [X] T072 [US3] Implement typed public `/api/v1` calls in `frontend/src/api/publicApi.ts`
- [X] T073 [US3] Implement typed internal/legacy generated access facade in `frontend/src/api/internalApi.ts`
- [X] T074 [P] [US3] Implement UI config DTO-to-domain adapter in `frontend/src/api/adapters/uiConfigAdapter.ts`
- [X] T075 [P] [US3] Implement entity DTO-to-domain adapter in `frontend/src/api/adapters/entityAdapter.ts`
- [X] T076 [P] [US3] Implement graph DTO-to-domain adapter in `frontend/src/api/adapters/graphAdapter.ts`
- [X] T077 [P] [US3] Implement table DTO-to-domain adapter in `frontend/src/api/adapters/tableAdapter.ts`
- [X] T078 [P] [US3] Implement dashboard DTO-to-domain adapter in `frontend/src/api/adapters/dashboardAdapter.ts`
- [X] T079 [P] [US3] Implement error DTO-to-domain adapter in `frontend/src/api/adapters/errorAdapter.ts`
- [X] T080 [US3] Replace direct generic UI imports from `frontend/src/api/client.ts` with `frontend/src/api/publicApi.ts` in `frontend/src/pages/SnapshotPage.tsx`
- [X] T081 [US3] Replace direct generic UI imports from `frontend/src/api/client.ts` with `frontend/src/api/publicApi.ts` in `frontend/src/pages/DashboardPage.tsx`
- [X] T082 [US3] Replace direct generic UI imports from `frontend/src/api/client.ts` with `frontend/src/api/publicApi.ts` in `frontend/src/pages/TablesPage.tsx`
- [X] T083 [US3] Add adapter tests proving generated DTOs do not leave `frontend/src/api/adapters/**` in `frontend/src/api/adapters/adapterBoundary.test.ts`
- [X] T084 [US3] Add import-boundary test forbidding generic components from importing `frontend/src/api/generated/**` in `frontend/src/api/generatedImportBoundary.test.ts`

---

## Phase 6: User Story 4 - Generic graph works with entities, relations, visual encodings, and graph lenses (Priority: P2)

**Goal**: Replace module-shaped graph assumptions with generic entity graph nodes, relation edges, graph lenses, and backend-defined visual encodings.

**Independent Test**: A graph lens containing non-module entities renders nodes, edges, filters, controls, tooltips, and visual encodings without `module_name` or fixed edge breakdowns.

### Implementation tasks

- [X] T085 [P] [US4] Define `EntityGraphNode`, `EntityGraphEdge`, `EntityGraphModel`, and `GraphLensDefinition` in `frontend/src/domain/graph.ts`
- [X] T086 [P] [US4] Define `VisualEncodingDefinition`, `VisualEncodingRole`, and `GraphVisualEncodingConfig` in `frontend/src/domain/visualEncoding.ts`
- [X] T087 [P] [US4] Implement metric accessor helpers for graph visual encodings in `frontend/src/visualization/metricAccessors.ts`
- [X] T088 [P] [US4] Implement graph size, color, thickness, badge, and label mapping in `frontend/src/visualization/visualEncoding.ts`
- [X] T089 [US4] Implement graph display model builder from generic graph plus visual encodings in `frontend/src/visualization/graphDisplayModel.ts`
- [X] T090 [P] [US4] Create generic graph layout adapter using existing d3-force behavior in `frontend/src/components/generic/graph/entityGraphLayout.ts`
- [X] T091 [P] [US4] Create generic graph tooltip builder using metric definitions and relation definitions in `frontend/src/components/generic/graph/entityGraphTooltips.ts`
- [X] T092 [US4] Implement `EntityGraph` component that renders `EntityGraphModel` and never reads `module_name` in `frontend/src/components/generic/graph/EntityGraph.tsx`
- [X] T093 [US4] Implement graph view model selector for filters, visible relations, labels, and visual encodings in `frontend/src/components/generic/graph/entityGraphViewModel.ts`
- [X] T094 [US4] Refactor `GraphSettingsPanel` to read graph filters and visual encoding options from `DefinitionRegistry` in `frontend/src/components/GraphSettingsPanel.tsx`
- [X] T095 [US4] Replace fixed edge breakdown labels with relation type definitions and fallback labels in `frontend/src/components/graphSelectors.ts`
- [X] T096 [US4] Convert `ModuleGraph` into a legacy wrapper that delegates to `EntityGraph` through a legacy graph adapter in `frontend/src/components/ModuleGraph.tsx`
- [X] T097 [US4] Add fixture for a non-module graph lens with unknown relation type in `frontend/src/components/generic/graph/__fixtures__/nonModuleGraph.ts`
- [X] T098 [US4] Add tests that `EntityGraph` renders without `module_name` and without fixed `breakdown` fields in `frontend/src/components/generic/graph/EntityGraph.test.tsx`

---

## Phase 7: User Story 5 - Generic tables and drilldowns work from backend table definitions (Priority: P2)

**Goal**: Render backend-provided table projections with columns, rows, values, row actions, and generic drilldown stack.

**Independent Test**: An unfamiliar table with unfamiliar columns and a row drilldown action renders and navigates without reading module/file fields.

### Implementation tasks

- [X] T099 [P] [US5] Define `TableDefinition`, `TableColumnDefinition`, `TableRow`, `TableProjection`, and `DrilldownFrame` in `frontend/src/domain/table.ts`
- [X] T100 [P] [US5] Implement generic table column normalization in `frontend/src/api/adapters/tableAdapter.ts`
- [X] T101 [P] [US5] Implement generic row action normalization in `frontend/src/api/adapters/tableAdapter.ts`
- [X] T102 [US5] Implement `GenericDataTable` using response columns and `GenericValueRenderer` in `frontend/src/components/generic/table/GenericDataTable.tsx`
- [X] T103 [US5] Implement drilldown stack state and action execution helpers in `frontend/src/components/generic/table/useDrilldownStack.ts`
- [X] T104 [US5] Refactor `TablesPage` to use `listTablesV1`, `getTableV1`, `GenericDataTable`, and `useDrilldownStack` in `frontend/src/pages/TablesPage.tsx`
- [X] T105 [US5] Refactor `ReportTables` into a legacy wrapper around `GenericDataTable` with no direct `row.cells.module_name` usage in `frontend/src/components/ReportTables.tsx`
- [X] T106 [US5] Remove client-side loading of all files for module drilldown from `SnapshotPage` and use table row actions instead in `frontend/src/pages/SnapshotPage.tsx`
- [X] T107 [US5] Represent relations as a generic table projection from `/api/v1/tables/{tableId}` in `src/ppi/query/projections.py`
- [X] T108 [US5] Ensure dynamic line-count values are emitted as explicit table columns in `src/ppi/query/projections.py`
- [X] T109 [US5] Add unfamiliar-column table fixture with drilldown row action in `frontend/src/components/generic/table/__fixtures__/genericTable.ts`
- [X] T110 [US5] Add tests for `GenericDataTable` unknown columns and row actions in `frontend/src/components/generic/table/GenericDataTable.test.tsx`
- [X] T111 [US5] Add tests for drilldown stack behavior in `frontend/src/components/generic/table/useDrilldownStack.test.ts`

---

## Phase 8: User Story 6 - Metrics dashboard validates queries from definitions (Priority: P2)

**Goal**: Dashboard controls and requests are driven by query definitions, entity kinds, metric definitions, target catalog, and supported aggregations.

**Independent Test**: Changing entity kind invalidates target, metric, or aggregation; the UI replaces invalid selections and never sends an invalid request.

### Implementation tasks

- [X] T112 [P] [US6] Define `QueryDefinition`, `QueryParameterDefinition`, `MetricQueryState`, and `MetricQueryResult` in `frontend/src/domain/query.ts`
- [X] T113 [P] [US6] Implement `getValidMetricsForEntityKind` using metric definitions in `frontend/src/transforms/dashboardTransforms.ts`
- [X] T114 [P] [US6] Implement `getValidAggregationsForMetric` using metric definitions in `frontend/src/transforms/dashboardTransforms.ts`
- [X] T115 [P] [US6] Implement `normalizeMetricQueryState` with deterministic first-valid fallback behavior in `frontend/src/transforms/dashboardTransforms.ts`
- [X] T116 [US6] Replace dashboard target loading from module tables with `listEntitiesV1` in `frontend/src/pages/DashboardPage.tsx`
- [X] T117 [US6] Replace hardcoded dashboard metric options with UI config query and metric definitions in `frontend/src/pages/DashboardPage.tsx`
- [X] T118 [US6] Replace dashboard aggregation options with metric-supported aggregations from `DefinitionRegistry` in `frontend/src/pages/DashboardPage.tsx`
- [X] T119 [US6] Prevent metrics timeseries and hotspot requests when normalized query state is unavailable in `frontend/src/pages/DashboardPage.tsx`
- [X] T120 [US6] Implement neutral unavailable dashboard state for missing valid metrics, targets, or aggregations in `frontend/src/pages/DashboardPage.tsx`
- [X] T121 [US6] Adapt `/api/v1/metrics/timeseries` responses into dashboard domain results in `frontend/src/api/adapters/dashboardAdapter.ts`
- [X] T122 [US6] Adapt `/api/v1/metrics/hotspots` responses into dashboard domain results in `frontend/src/api/adapters/dashboardAdapter.ts`
- [X] T123 [US6] Add tests for dashboard query normalization invalidating metric, target, and aggregation in `frontend/src/transforms/dashboardTransforms.test.ts`
- [X] T124 [US6] Add component test proving Dashboard does not issue invalid requests in `frontend/src/pages/DashboardPage.test.tsx`

---

## Phase 9: User Story 7 - Legacy compatibility is contained and removable (Priority: P3)

**Goal**: Keep old domain-shaped endpoints and DTOs working only behind an explicit legacy boundary, with checks preventing generic code from depending on them.

**Independent Test**: Import-boundary and forbidden-string checks fail if generic frontend code imports legacy modules or references banned identifiers.

### Implementation tasks

- [X] T125 [P] [US7] Move legacy frontend DTO declarations copied from `api/client.ts` into `frontend/src/legacy/legacyApiTypes.ts`
- [X] T126 [P] [US7] Implement `legacyGraphToGenericGraph` in `frontend/src/legacy/legacyGraphAdapter.ts`
- [X] T127 [P] [US7] Implement `legacySnapshotToGenericTables` in `frontend/src/legacy/legacyTableAdapter.ts`
- [X] T128 [P] [US7] Implement `legacyMetricsToDefinitions` in `frontend/src/legacy/legacyDashboardAdapter.ts`
- [X] T129 [P] [US7] Move temporary Odoo/Python labels into `frontend/src/legacy/legacyOdooLabels.ts`
- [X] T130 [US7] Remove generic imports from `frontend/src/registry/odooProfile.ts` and keep that file legacy-only in `frontend/src/registry/odooProfile.ts`
- [X] T131 [US7] Add forbidden identifier scanner for generic frontend paths in `scripts/check_frontend_boundaries.py`
- [X] T132 [US7] Configure the boundary scanner to fail on `module_name`, `python_file_count`, `cyclomatic`, `cognitive`, `jones`, `manifest_depends`, `model_reuse`, `field_property`, `extension_or_method`, `python_lines`, `xml_lines`, `score_in`, and `score_out` in `scripts/check_frontend_boundaries.py`
- [X] T133 [US7] Add npm script `check:frontend-boundaries` that runs the boundary scanner in `frontend/package.json`
- [X] T134 [US7] Add tests proving generic frontend paths do not import legacy modules in `frontend/src/legacy/legacyBoundary.test.ts`
- [X] T135 [US7] Add documentation for allowed legacy imports and removal rules in `frontend/src/legacy/README.md`

---

## Phase 10: User Story 8 - API contract governance prevents accidental public API drift (Priority: P3)

**Goal**: Lint, bundle, generate, and diff the API contract, with non-blocking diffs before baseline and blocking breaking-change detection after baseline.

**Independent Test**: Removing an operationId fails linting; removing a response field appears in a diff report; after baseline, breaking public `/api/v1` changes can be made blocking.

### Implementation tasks

- [X] T136 [US8] Ensure `scripts/export_openapi.py` writes deterministic JSON with sorted keys to `openapi/openapi.json`
- [X] T137 [US8] Ensure `scripts/check_openapi.sh` runs export, Spectral lint, Redocly lint, Redocly bundle, and frontend type generation in order in `scripts/check_openapi.sh`
- [X] T138 [US8] Ensure `scripts/diff_openapi.sh` succeeds without a baseline and prints a clear message in `scripts/diff_openapi.sh`
- [X] T139 [US8] Add placeholder current baseline instructions and baseline promotion steps in `openapi/baseline/README.md`
- [X] T140 [US8] Add bundled OpenAPI output generation target for `openapi/openapi.bundle.yaml` in `scripts/check_openapi.sh`
- [X] T141 [US8] Add API contract workflow to CI or local validation documentation in `.github/workflows/api-contract.yml`
- [X] T142 [US8] Add test fixture that fails when a public operation lacks operationId in `tests/server/test_openapi_governance.py`
- [X] T143 [US8] Add test fixture that fails when public `/api/v1` schema fields are not `camelCase` in `tests/server/test_openapi_governance.py`
- [X] T144 [US8] Add documentation for experimental `/api/v1`, baseline promotion, deprecation policy (sunset timeline, migration path, deprecation headers distinct from breaking-change detection), and post-baseline breaking-change policy in `docs/api-versioning-policy.md`

---

## Phase 11: Polish and Cross-Cutting Validation

- [X] T145 Run backend tests and fix only issues introduced by `/api/v1` changes in `tests/server/test_api_v1_openapi.py`
- [X] T146 Run frontend typecheck and fix only generated-client or adapter typing errors in `frontend/tsconfig.json`
- [X] T147 Run frontend tests and fix only generic renderer, graph, table, dashboard, and boundary failures in `frontend/vitest.config.ts`
- [X] T148 Run OpenAPI export and commit updated generated types in `frontend/src/api/generated/schema.d.ts`
- [X] T149 Run API lint and bundle and commit `openapi/openapi.json` plus `openapi/openapi.bundle.yaml`
- [X] T150 Run non-blocking API diff report and store output instructions in `openapi/baseline/README.md`
- [X] T151 Run forbidden-domain-string boundary scan and remove violations from generic paths in `scripts/check_frontend_boundaries.py`
- [X] T152 Update `quickstart.md` validation results after implementation in `specs/010-frontend-api-platform/quickstart.md`
- [X] T153 Update architecture notes with the new principle “OpenAPI owns transport contract; frontend domain owns rendering primitives” in `docs/architecture.md`
- [X] T154 Add a migration status checklist for Graph, Tables, Metrics Dashboard, legacy adapters, and baseline readiness in `docs/frontend-api-platform-migration.md`

---

## Dependencies

### Phase dependencies

```text
Phase 1 Setup
  -> Phase 2 Foundation
  -> Phase 3 US1 Generic metadata frontend
  -> Phase 4 US2 API v1 contract
  -> Phase 5 US3 Generated transport and adapters
  -> Phase 6 US4 Graph
  -> Phase 7 US5 Tables
  -> Phase 8 US6 Metrics Dashboard
  -> Phase 9 US7 Legacy boundary
  -> Phase 10 US8 Governance
  -> Phase 11 Polish
```

### Story dependencies

- **US1** depends on Phase 2 because generic frontend primitives and UI config provider need the foundational file structure.
- **US2** depends on Phase 2 because `/api/v1` schemas, router, and error handling must exist before endpoints are implemented.
- **US3** depends on US2 because generated transport types require exported OpenAPI for `/api/v1`.
- **US4** depends on US1 and US3 because graph uses generic domain definitions and public API adapters.
- **US5** depends on US1 and US3 because tables use generic domain definitions and public API adapters.
- **US6** depends on US1 and US3 because dashboard uses generic metric/query definitions and public API adapters.
- **US7** can start after US3 but must finish before declaring Graph, Tables, and Metrics Dashboard migrated.
- **US8** can start after US2 but becomes fully useful after US3 produces generated types.

---

## Parallel Execution Examples

### After Phase 2 is complete

```text
Agent A: T026-T045  # domain primitives, registry, value renderers
Agent B: T046-T068  # /api/v1 schemas, endpoints, projections
Agent C: T125-T135  # legacy boundary and forbidden-string checks
```

### After US1, US2, and US3 are complete

```text
Agent A: T085-T098  # generic graph migration
Agent B: T099-T111  # generic tables migration
Agent C: T112-T124  # metrics dashboard migration
Agent D: T136-T144  # API governance hardening
```

---

## Independent Test Criteria by Story

- **US1**: Unknown metric, relation type, line category, and entity kind render through definitions or fallback labels without runtime crash.
- **US2**: OpenAPI export contains `/api/v1` endpoints with `camelCase` fields, stable operationIds, tags, summaries, response models, and `ErrorResponse`.
- **US3**: Generic frontend components do not import generated DTOs directly; generated DTOs enter generic code only through adapters.
- **US4**: Graph renders a non-module entity graph without `module_name`, fixed edge breakdowns, or hardcoded visual metric options.
- **US5**: Tables render unknown columns and execute backend-provided drilldown actions without reading module/file fields.
- **US6**: Dashboard normalizes invalid entity/target/metric/aggregation combinations and does not send invalid requests.
- **US7**: Boundary checks fail when generic frontend code imports legacy modules or contains forbidden domain identifiers.
- **US8**: API linting catches missing operationIds/tags/summaries and diff reporting produces a non-blocking report before baseline.

---

## Suggested MVP Scope

Implement the MVP in this exact order:

1. Phase 1 Setup.
2. Phase 2 Foundation.
3. US2 `/api/v1` public contract and generic projections.
4. US1 frontend domain primitives, `UiConfigProvider`, `DefinitionRegistry`, and value renderers.
5. US3 generated transport, public API facade, and adapters.
6. US5 generic Tables migration.
7. US4 generic Graph migration.
8. US6 Metrics Dashboard migration.
9. US7 boundary checks.
10. US8 governance hardening.

Do not declare `/api/v1` stable during MVP. It remains experimental until Graph, Tables, and Metrics Dashboard all satisfy their migration gates.

---

## Implementation Strategy

1. Keep legacy endpoints running while `/api/v1` is introduced.
2. Implement public `/api/v1` DTOs with Pydantic aliases so JSON and OpenAPI use `camelCase`.
3. Generate frontend transport types from OpenAPI before migrating generic components.
4. Create frontend domain types by hand and keep them separate from generated DTOs.
5. Convert all public DTOs through `frontend/src/api/adapters/**`.
6. Migrate Tables before Graph because table projections are simpler and prove the generic renderer path.
7. Migrate Graph next using generic graph projections, graph lenses, and visual encodings.
8. Migrate Metrics Dashboard after entity targets, metric definitions, and query definitions are reliable.
9. Add legacy boundary checks before removing old imports.
10. Add API governance checks and keep `oasdiff` non-blocking until the stable baseline is explicitly promoted.

## Phase 12: Ambiguity Hardening Tasks

**Goal**: Convert the analysis hardening decisions into concrete validation and documentation work so weaker models do not infer alternatives.

- [X] T155 [P] Link spec/plan to existing `.specify/memory/constitution.md` v1.1.1 and add an alignment cross-reference table to `plan.md` §12 (constitution already exists; do not create a new one)
- [X] T156 [P] Add latest-commit selection test using greatest `commitOrder` in `tests/server/test_api_v1_defaults.py`
- [X] T157 [P] Add store-not-ready `ErrorResponse` test for `/api/v1/status`, `/api/v1/graph`, and `/api/v1/tables/{tableId}` in `tests/server/test_api_v1_errors.py`
- [X] T158 [P] Add OpenAPI property-name test that fails on underscores in public `/api/v1` schema properties in `tests/server/test_openapi_governance.py`
- [X] T159 Add deterministic fallback-label unit tests for dotted, snake_case, kebab-case, slash-separated, empty, and whitespace identifiers in `frontend/src/registry/fallbackLabels.test.ts`
- [X] T160 Add generic value renderer tests for unknown value type fallback, null display, boolean display, and escaped string display in `frontend/src/components/generic/values/GenericValueRenderer.test.tsx`
- [X] T161 Add adapter fixture rule tests for happy path, unknown id, missing optional arrays, and legacy field leakage in `frontend/src/api/adapters/adapterContract.test.ts`
- [X] T162 Add boundary scanner import checks for generated DTO imports in `scripts/check_frontend_boundaries.py`
- [X] T163 Add boundary scanner import checks for legacy imports in generic/domain/registry paths in `scripts/check_frontend_boundaries.py`
- [X] T164 Add boundary scanner violation output with file path, line number, and token/import in `scripts/check_frontend_boundaries.py`
- [X] T165 Add table row action params documentation to `docs/frontend-api-platform-migration.md`
- [X] T166 Add page migration state matrix for Graph, Tables, and Metrics Dashboard to `docs/frontend-api-platform-migration.md`
- [X] T167 Add explicit generated DTO ownership note to `frontend/src/api/README.md`
- [X] T168 Add `MetricQueryStateResult` type and no-request rule to `frontend/src/domain/query.ts`
- [X] T169 Add tests proving Dashboard sends requests only for `MetricQueryStateResult.status === "valid"` in `frontend/src/pages/DashboardPage.test.tsx`
- [X] T170 Add non-blocking missing-baseline message to `scripts/diff_openapi.sh`
- [X] T171 Add baseline promotion instructions copying `openapi/openapi.json` to `openapi/baseline/current.json` only after migration gate in `openapi/baseline/README.md`
- [X] T172 Add HTTP status mapping tests for invalid query, missing table/lens, unavailable store, and unexpected errors in `tests/server/test_api_v1_errors.py`
- [X] T173 Add projection-layer test proving `/api/v1` handlers delegate data shaping instead of embedding frontend transformation logic in `tests/server/test_api_v1_projection_boundaries.py`
- [X] T173a Add diagnostics-exclusion test proving default `/api/v1` graph, table, and dashboard projections do not include `evidence`, `parse_errors`, or diagnostics-only fields unless the diagnostics capability is explicitly requested in `tests/server/test_api_v1_diagnostics_exclusion.py`
- [X] T173b Add canonical-vs-projection test proving `projections.py` distinguishes canonical analysis records from UI graph/table/dashboard/treemap/diagnostics projections in `tests/server/test_api_v1_projection_boundaries.py`
- [X] T174 Add comments in `src/ppi/query/projections.py` naming it as the only initial backend generic projection layer
- [X] T175 Add `camelCase` alias serialization test for one representative schema from status, graph, table, metrics, and error responses in `tests/server/test_api_v1_camel_case.py`
- [X] T176 Add `publicApi` facade test proving returned objects contain domain fields and no raw generated DTO wrapper in `frontend/src/api/publicApi.test.ts`
- [X] T177 Add docs that legacy labels belong in backend profile metadata or `frontend/src/legacy/legacyOdooLabels.ts`, not generic renderers, in `frontend/src/legacy/README.md`
- [X] T178 Run the new implementation-readiness checklist and mark each item in `specs/010-frontend-api-platform/checklists/implementation-readiness.md`
- [X] T179 Re-run Specification Analysis after T155-T178 and update `specs/010-frontend-api-platform/analysis-report.md`
- [X] T180 Export the hardened workspace archive after all artifact edits in `scripts/export_workspace.py`
