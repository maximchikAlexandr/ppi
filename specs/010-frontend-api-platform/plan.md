# Implementation Plan: Frontend Platform and Public API Contract Foundation

**Feature**: `010-frontend-api-platform`  
**Title**: Frontend Platform and Public API Contract Foundation  
**Spec**: `specs/010-frontend-api-platform/spec.md`  
**Plan Status**: completed  
**Date**: 2026-07-08

## 1. Implementation Goal

Build a frontend platform layer and a versioned API contract foundation so generic frontend code does not depend on Python/Odoo-specific fields, hardcoded metric identifiers, module-shaped graph nodes, fixed edge breakdowns, or legacy table shapes.

The implementation MUST migrate the main generic views to the following architecture:

```text
Backend facts/storage/query layer
  -> backend projection builders
  -> /api/v1 camelCase REST DTOs
  -> exported OpenAPI contract
  -> generated frontend transport types/client
  -> frontend adapters
  -> frontend domain model
  -> view models
  -> React components
```

Do not implement a second generic abstraction on top of legacy `/api/*` endpoints as a permanent solution. Legacy endpoints may remain only behind explicitly named legacy adapters.

## 2. Current Code Context

### Backend

- The package is Python 3.11+ and already depends on FastAPI and Pydantic v2.
- Existing HTTP endpoints are in `src/ppi/server/api.py` and currently use unversioned paths such as `/status`, `/graph`, `/snapshot/modules`, `/metrics/timeseries`, and `/hotspots`.
- Existing shared response schemas are in `src/ppi/query/schemas.py` and are domain-shaped: module snapshots, file snapshots, fixed line categories, fixed edge breakdown categories, evidence rows, and Python/Odoo-specific metrics.
- Existing API parameter validation still uses hardcoded domain patterns such as `module|file` and fixed metric ids.

### Frontend

- Frontend stack is React 18, TypeScript, Vite, Mantine, Recharts, d3-force, d3-hierarchy, zod, i18next, Vitest.
- Existing frontend transport code is in `frontend/src/api/client.ts` and manually declares DTOs.
- Existing runtime boundary validation is in `frontend/src/api/schemas.ts` and contains closed domain enums for edge kinds, breakdown kinds, and line categories.
- Existing components and pages still read domain-specific fields such as `module_name`, `python_file_count`, `cyclomatic`, `cognitive`, `jones`, `manifest_depends`, `breakdown`, and `line_categories`.

## 3. Non-Negotiable Decisions

The implementation MUST follow these decisions exactly.

1. Public/generic API JSON uses `camelCase`.
2. Python implementation fields may remain `snake_case`, but public Pydantic response/request models MUST expose `camelCase` aliases in OpenAPI and JSON.
3. New public/generic endpoints live under `/api/v1`.
4. Old `/api/*` endpoints remain legacy and MUST NOT be used by new generic components except through `frontend/src/legacy/**` adapters.
5. Generated frontend transport types/client are generated from the full OpenAPI contract.
6. Generic frontend code MUST import only the public/generic API facade and frontend domain models, not generated DTOs directly.
7. Legacy/internal generated access MAY exist, but it MUST be isolated behind legacy/internal adapter modules.
8. `/api/v1` remains experimental until Graph, Tables, and Metrics Dashboard all use generated transport access plus explicit domain adapters.
9. The first stable `/api/v1` baseline is declared only after the Graph, Tables, and Metrics Dashboard migration gate is complete.
10. API diff reporting is non-blocking before the first stable baseline.
11. Breaking-change detection becomes blocking for public `/api/v1` endpoints after the first stable baseline.
12. `openapi-typescript` and `openapi-fetch` are the first frontend transport generation tools.
13. Spectral and Redocly CLI are the first API governance tools.
14. `oasdiff` is added as non-blocking diff reporting before baseline.
15. Orval, Hey API, Zally, and AIP linter are not part of this implementation phase.
16. Google AIP and Zalando guidelines may inform naming/style, but compliance is not required.

## 4. Technical Context

### Backend Runtime

- Python: `>=3.11`
- Framework: FastAPI
- Schema boundary: Pydantic v2 for public REST/OpenAPI models
- Internal contracts: keep existing Python style; do not force camelCase into internal query/storage code
- OpenAPI version: 3.1 through FastAPI export
- API router structure:

```text
src/ppi/server/
  api.py                    # legacy router remains
  api_v1.py                 # new public/generic /api/v1 router
  v1_schemas.py             # public/generic Pydantic models with camelCase aliases (FastAPI boundary)
  openapi.py                # OpenAPI export/customization helpers

src/ppi/query/
  schemas.py                # legacy schemas remain
  projections.py            # generic projection builders (core; returns plain structures, no Pydantic)
  v1_handlers.py            # v1 query handlers delegating to projections (thin FastAPI glue)
```

Constitution Principle VI requires Pydantic ONLY at the FastAPI boundary. `v1_schemas.py` therefore lives in `src/ppi/server/` next to `api_v1.py`, and `projections.py` stays in `src/ppi/query/` returning plain dicts/`msgspec`-compatible structures. `v1_handlers.py` is thin FastAPI glue that converts projection output into Pydantic response models.

### Frontend Runtime

- React 18
- TypeScript
- Vite
- Mantine remains UI component library
- Existing d3-force/d3-hierarchy remain visualization engines
- Zod remains allowed for legacy/webview/raw bridge validation, but public REST DTO source of truth becomes generated OpenAPI types
- Generated transport client:

```text
frontend/src/api/generated/schema.d.ts
frontend/src/api/generated/client.ts
frontend/src/api/http.ts
frontend/src/api/publicApi.ts
frontend/src/api/internalApi.ts
```

### Frontend Platform Layout

Create this structure:

```text
frontend/src/domain/
  ids.ts
  metric.ts
  entity.ts
  relation.ts
  graph.ts
  table.ts
  filter.ts
  action.ts
  visualEncoding.ts
  capability.ts
  page.ts

frontend/src/registry/
  UiConfigProvider.tsx
  DefinitionRegistry.ts
  uiConfigTypes.ts
  fallbackLabels.ts

frontend/src/api/adapters/
  uiConfigAdapter.ts
  entityAdapter.ts
  graphAdapter.ts
  tableAdapter.ts
  dashboardAdapter.ts
  errorAdapter.ts

frontend/src/legacy/
  legacyApiTypes.ts
  legacyGraphAdapter.ts
  legacyTableAdapter.ts
  legacyDashboardAdapter.ts
  legacyOdooLabels.ts

frontend/src/components/generic/
  values/
    GenericValueRenderer.tsx
    MetricValueRenderer.tsx
    NumberValueRenderer.tsx
    DateValueRenderer.tsx
    BooleanValueRenderer.tsx
  table/
    GenericDataTable.tsx
  graph/
    EntityGraph.tsx
    entityGraphViewModel.ts
    entityGraphLayout.ts
    entityGraphTooltips.ts
```

## 5. Public API Shape

Implement these `/api/v1` endpoints first. Do not add extra endpoints during this phase unless required by these contracts.

```text
GET  /api/v1/status
GET  /api/v1/ui/config
GET  /api/v1/commits
GET  /api/v1/entities?entityKindId={id}&commitId={commitId}
GET  /api/v1/graph?lensId={lensId}&commitId={commitId}&includeZeroWeight={boolean}
GET  /api/v1/tables
GET  /api/v1/tables/{tableId}?commitId={commitId}&parentEntityId={id}
GET  /api/v1/metrics/timeseries?entityKindId={id}&metricId={id}&aggregation={id}&targetId={id?}
GET  /api/v1/metrics/hotspots?entityKindId={id}&metricId={id}&aggregation={id}&rankBy={value|growth}&limit={n}
```

All public JSON fields MUST be camelCase. Examples: `commitId`, `entityKindId`, `metricId`, `relationTypeId`, `tableId`, `valueType`, `defaultVisible`.

## 6. Error Contract

All `/api/v1` errors MUST use this response shape:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {},
    "requestId": "string"
  }
}
```

Rules:

- `code` is stable and machine-readable.
- `message` is human-readable and safe to show in development UI.
- `details` is optional and must be JSON-serializable.
- `requestId` is optional in local mode but the field must be present in schema.
- Do not return FastAPI default validation errors directly from public `/api/v1` endpoints.

## 7. API Governance Tooling

Add root-level API artifacts and scripts:

```text
openapi/openapi.json
openapi/openapi.bundle.yaml
openapi/baseline/README.md
.spectral.yaml
redocly.yaml
scripts/export_openapi.py
scripts/check_openapi.sh
scripts/diff_openapi.sh
```

Required commands:

```bash
uv run python scripts/export_openapi.py --output openapi/openapi.json
npx spectral lint openapi/openapi.json
npx redocly lint openapi/openapi.json
npx redocly bundle openapi/openapi.json -o openapi/openapi.bundle.yaml
npx openapi-typescript openapi/openapi.json -o frontend/src/api/generated/schema.d.ts
npx oasdiff changelog openapi/baseline/current.json openapi/openapi.json
```

Before the first stable baseline, `oasdiff` produces a report but does not fail the build. After the baseline is declared, `oasdiff breaking` fails on breaking public `/api/v1` changes.

## 8. Frontend Generated Client Rules

Generated types/client may cover the full OpenAPI contract, including legacy and internal endpoints. Usage is restricted:

```text
Allowed in generic frontend:
  frontend/src/api/publicApi.ts
  frontend/src/api/adapters/**
  frontend/src/domain/**
  frontend/src/components/generic/**

Forbidden in generic frontend:
  direct import from frontend/src/api/generated/**
  direct import from frontend/src/legacy/**
  direct use of legacy DTO field names
```

`frontend/src/api/publicApi.ts` is the only public/generic API facade consumed by generic pages and components.

## 9. Frontend Migration Gate

The first stable `/api/v1` baseline requires all three views below to use generated transport access plus explicit adapters:

1. Graph view
2. Tables view
3. Metrics Dashboard

A migrated view satisfies all conditions:

- Uses `/api/v1` public facade.
- Does not call legacy `fetchGraph`, `fetchSnapshotModules`, `fetchSnapshotFiles`, `fetchTimeseries`, or `fetchHotspots` directly.
- Does not import generated DTOs directly in React components.
- Does not read `module_name`, `python_file_count`, `cyclomatic`, `cognitive`, `jones`, `manifest_depends`, `breakdown.model_reuse`, or `python_lines` outside `frontend/src/legacy/**`.
- Renders from frontend domain/view models.

## 10. Implementation Phases

### Phase 1 — API and Frontend Boundary Foundation

Create `/api/v1`, OpenAPI export, common error shape, Spectral, Redocly, generated TypeScript types, generated fetch client, `UiConfigProvider`, `DefinitionRegistry`, and domain model skeleton.

Exit criteria:

- `openapi/openapi.json` exists.
- OpenAPI lint passes.
- Generated TypeScript DTOs exist.
- Generic frontend code can load `UiConfig` through provider.
- Legacy endpoints still work.

### Phase 2 — Backend Generic Projections

Create backend projection builders for UI config, graph, tables, entities, metrics timeseries, and hotspots.

Exit criteria:

- `/api/v1/ui/config` returns all definitions required by Graph, Tables, and Metrics Dashboard.
- `/api/v1/graph` returns generic nodes/edges.
- `/api/v1/tables/{tableId}` returns columns/rows/actions.
- `/api/v1/entities` returns targets by entity kind.
- `/api/v1/metrics/*` accepts entityKind/metric/aggregation/target parameters.

### Phase 3 — Frontend Domain Adapters

Implement adapters from generated transport DTOs to frontend domain models.

Exit criteria:

- Adapter tests cover unknown metric, relation type, entity kind, line category, and table column.
- Generic components receive no transport DTOs.
- Unknown identifiers render fallback labels.

### Phase 4 — Graph Migration

Introduce `EntityGraph` and migrate graph page to `/api/v1/graph` plus visual encoding definitions.

Exit criteria:

- Graph works without `module_name` as required ID.
- Graph settings are config-driven.
- Edge/relation labels come from definitions or fallback.
- Legacy `ModuleGraph` is only a wrapper or no longer used by migrated page.

### Phase 5 — Tables Migration

Introduce `GenericDataTable`, generic row actions, and drilldown stack.

Exit criteria:

- Tables page uses `/api/v1/tables/{tableId}`.
- Relations render as generic table.
- Module/file drilldown uses row actions, not `module_name`.
- Dynamic line-count columns are explicit table columns.

### Phase 6 — Metrics Dashboard Migration

Migrate dashboard to query definitions, entity kind targets, metric definitions, and aggregation validation.

Exit criteria:

- Dashboard uses `/api/v1/entities` and `/api/v1/metrics/*`.
- Invalid entity kind/target/metric/aggregation combinations cannot be submitted.
- Dashboard does not rely on `level: module|file` except in legacy adapter tests.

### Phase 7 — Governance and Baseline Preparation

Add oasdiff report and prepare baseline docs.

Exit criteria:

- `oasdiff` report runs non-blocking.
- Baseline README explains when to declare stable.
- Stable baseline is not declared until Graph, Tables, and Metrics Dashboard exit criteria pass.

### Phase 8 — Cleanup and Enforcement

Add import-boundary checks and forbidden identifier checks.

Exit criteria:

- Generic code cannot import legacy modules.
- Generic code cannot import generated DTOs directly.
- Forbidden domain identifiers fail validation outside allowed paths.

## 11. Testing Strategy

### Backend Tests

Add tests for:

- `/api/v1` route availability.
- camelCase JSON output.
- OpenAPI includes camelCase public schemas.
- common error response shape.
- UI config contains definitions required by Graph, Tables, Dashboard.
- graph projection uses generic node/edge shapes.
- table projection includes columns and row ids.
- metrics endpoints reject invalid metric/entity/aggregation combinations with common error shape.

### Frontend Tests

Add tests for:

- `DefinitionRegistry` lookup and fallback labels.
- adapters for UI config, graph, table, dashboard.
- unknown plugin-like data fixtures.
- `GenericValueRenderer` formatting.
- `EntityGraph` view model without module-specific fields.
- generic table drilldown action handling.
- dashboard query state normalization.
- import-boundary and forbidden identifier validation.

### Contract Tests

Add tests for:

- OpenAPI export command.
- Spectral lint.
- Redocly lint/bundle.
- generated TypeScript types compile.
- public facade typechecks after generation.
- oasdiff report command works non-blocking before baseline.

## 12. Constitution Check

Constitution: `.specify/memory/constitution.md` v1.1.1 (ratified 2026-06-19, last amended 2026-07-05).

| Principle | Requirement | Alignment |
|---|---|---|
| II. Layered Core Independence | FR-002/FR-003 forbid Python/Odoo concepts in generic frontend; backend query layer stays core-only | Aligned. `/api/v1` Pydantic schemas live at the FastAPI boundary (see §4); `projections.py` returns plain dicts/structures, not Pydantic models. |
| IV. CLI-First, Multi-Interface Clients | Spec requires generic UI over registry of entity kinds, metric definitions, edge layers, active profile | Aligned. FR-001..FR-011 define registry-driven generic UI; no Python/Odoo hard-wiring. |
| VI. Typed Contracts & Explicit Error Handling | Pydantic ONLY at FastAPI boundary; msgspec for internal contracts | Aligned. `v1_schemas.py` is the FastAPI OpenAPI/JSON boundary artifact; `projections.py` returns data structures (dict/`msgspec`-compatible), not Pydantic models. `ErrorResponse` (§6) is Pydantic only because it is part of the public HTTP contract. |

Cross-reference: `.specify/memory/constitution.md` v1.1.1 ratifies
Principles II, IV, and VI. This plan does not amend the constitution
or create a new one — the alignment is verified against the existing
ratified document.

No constitution violations found. Amendments to spec/plan that deviate from Principles II/IV/VI MUST be justified in the plan's Complexity Tracking table or rejected.

## 13. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Refactor becomes too large to review | Use strict phases and keep legacy endpoints working until generic view migration succeeds. |
| Generated SDK leaks into generic components | Add import-boundary checks and expose only `publicApi.ts` to generic code. |
| camelCase aliases diverge from Python internals | Require OpenAPI export tests and response JSON tests for `/api/v1`. |
| UI config becomes incomplete | Add fixture tests requiring Graph, Tables, and Dashboard definitions. |
| Legacy code remains forever | Put all legacy adapters under `frontend/src/legacy/**` and add cleanup tasks after migration. |

## 14. Deliverables Produced by This Plan

- `plan.md`
- `research.md`
- `data-model.md`
- `contracts/api-contract.md`
- `contracts/frontend-platform-contract.md`
- `contracts/governance-contract.md`
- `contracts/migration-boundaries.md`
- `quickstart.md`

## 15. Next Phase

Run `speckit-tasks` to create dependency-ordered implementation tasks. The tasks must follow the phases in this plan and must not introduce alternative architecture choices.

## 16. Weak-Model Execution Guardrails

Use these rules when an implementation model is likely to over-generalize or invent structure.

### 16.1 Do first, exactly once

1. Add `/api/v1` router and keep legacy routes registered.
2. Add `src/ppi/server/v1_schemas.py` with the camelCase alias base model and common error models (FastAPI boundary).
3. Add `projections.py` and route all new endpoint data shaping through it.
4. Add generated-client scripts before writing generic frontend API calls.
5. Add `publicApi.ts` facade before migrating pages.
6. Add boundary scanner before marking pages migrated.

### 16.2 Do not do

- Do not replace all old dashboard code at once. Migrate Graph, Tables, then Metrics Dashboard behind adapters.
- Do not use generated OpenAPI DTOs as React props for generic components.
- Do not copy legacy DTO fields into `domain/` types.
- Do not hardcode the existing Odoo profile as the generic platform default.
- Do not convert `snake_case` to `camelCase` manually in every endpoint; use model aliases and tests.
- Do not mark `/api/v1` stable from code; write only `experimental` or `baselineReady` until a human promotes a baseline.

### 16.3 Exact current-repository anchors

The referenced repository currently has a Python CLI/server under `src/ppi`, a React frontend under `frontend`, tests under `tests`, and a VS Code bridge under `vscode-extension`. This feature must preserve existing CLI flows and the current dashboard routes while adding the generic platform layer.

### 16.4 Required implementation order for weak agents

When tasks appear parallel, still apply this safe order unless a human intentionally parallelizes work:

```text
T001-T010
T011-T025
T046-T070
T026-T045
T071-T082
T083-T097
T098-T111
T112-T124
T125-T135
T136-T154
T155-T180
```

Rationale: the API schema and generated transport must exist before page migrations, and the generic definitions must exist before generic graph/table/dashboard rendering.

### 16.5 Validation command expectation

A complete implementation should be able to run these commands without relying on hidden IDE state:

```bash
uv run pytest
cd frontend && npm run typecheck
cd frontend && npm test
bash scripts/check_openapi.sh
bash scripts/diff_openapi.sh
cd frontend && npm run check:frontend-boundaries
```

If the project uses different existing frontend script names, add aliases rather than changing this specification's validation intent.
