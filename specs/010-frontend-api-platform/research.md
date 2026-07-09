# Research: Frontend Platform and Public API Contract Foundation

**Feature**: `010-frontend-api-platform`  
**Status**: completed  
**Rule for implementers**: Decisions in this file are final for this feature. Do not re-open alternatives during implementation.

## R-001: Public API namespace

**Decision**: New generic/public REST endpoints MUST use `/api/v1`.

**Rationale**: Existing unversioned endpoints are domain-shaped and cannot be treated as a future public contract without causing churn. A versioned namespace lets new frontend work use a clean contract while legacy endpoints remain available.

**Alternatives considered and rejected**:

- Reusing existing `/api/*`: rejected because it preserves domain-shaped contracts.
- Creating only `/api/internal/*`: rejected because the feature explicitly prepares a future public REST surface.
- Waiting for `/api/v2`: rejected because no stable v1 exists yet.

## R-002: REST field naming

**Decision**: Public `/api/v1` JSON and generated SDK types MUST use `camelCase`. Python code MAY keep internal Pydantic fields in `snake_case` and expose `camelCase` using aliases.

**Rationale**: The public consumer is TypeScript/frontend, and generated SDK ergonomics are better with `camelCase`. Pydantic aliases let Python internals stay idiomatic.

**Alternatives considered and rejected**:

- `snake_case` public JSON: rejected after clarification because the desired public SDK shape is `camelCase`.
- Supporting both `snake_case` and `camelCase`: rejected because it increases contract complexity and test burden.

## R-003: Generated frontend client scope

**Decision**: The generated transport layer MAY be generated from the full OpenAPI contract, including legacy/internal endpoints. Generic frontend code MUST use only the public/generic facade or explicit adapters.

**Rationale**: Full generation avoids maintaining multiple OpenAPI subsets initially. Import boundaries prevent generic code from depending directly on legacy/internal operations.

**Alternatives considered and rejected**:

- Generate only public `/api/v1`: rejected by clarification.
- Generate separate public/internal SDKs now: rejected because it adds infrastructure before contract shape stabilizes.

## R-004: Frontend domain model

**Decision**: Frontend domain models MUST be hand-written. Generated API DTOs MUST NOT become frontend domain models.

**Rationale**: API DTOs describe transport. Frontend domain models describe rendering primitives and interaction state. Mixing them would recreate the current tight coupling.

**Alternatives considered and rejected**:

- Use generated DTOs directly in components: rejected because generic components would depend on transport shape.
- Generate domain models from OpenAPI: rejected because OpenAPI cannot express frontend view semantics well enough.

## R-005: UI configuration

**Decision**: `/api/v1/ui/config` is the bootstrap source of truth for definitions, capabilities, visual encodings, query definitions, and page availability.

**Rationale**: Generic UI rendering requires metadata before rendering graph, tables, and dashboard. Hardcoded frontend registries would block plugin compatibility.

**Alternatives considered and rejected**:

- Keep `odooProfile.ts` as source of truth: rejected because it makes frontend own domain semantics.
- Split definitions across many endpoints first: rejected because initial bootstrapping would be fragile.

## R-006: API governance tools

**Decision**: Use Spectral, Redocly CLI, openapi-typescript, openapi-fetch, and oasdiff. Spectral and Redocly are blocking once wired. oasdiff is non-blocking before the first stable baseline.

**Rationale**: These tools provide linting, validation/bundling, typed transport generation, and diff reporting without forcing a heavyweight generated application data layer.

**Alternatives considered and rejected**:

- Orval now: rejected because generated hooks are premature before deciding on TanStack Query.
- Hey API now: rejected because it is better suited after a stable external SDK target exists.
- Zally now: rejected because Zalando-specific rules would add noise before the project style guide is stable.
- AIP linter now: rejected because the project does not expose protobuf API definitions.

## R-007: Stability baseline

**Decision**: `/api/v1` remains experimental until Graph, Tables, and Metrics Dashboard use generated transport access plus explicit domain adapters. After that baseline, breaking changes to public `/api/v1` endpoints become blocking.

**Rationale**: These three views contain the largest domain leakage and are the minimum useful public/generic frontend surface. Declaring baseline earlier would freeze incomplete contracts.

**Alternatives considered and rejected**:

- Stable immediately: rejected because it blocks necessary API refactor.
- Stable only after external SDK publication: rejected because it delays contract discipline too long.
- Stable after Graph/Tables only: rejected after clarification because Metrics Dashboard must also migrate.

## R-008: Legacy compatibility

**Decision**: Legacy endpoints and DTOs remain during migration but MUST be isolated under `frontend/src/legacy/**` or explicitly named internal API boundaries.

**Rationale**: Removing all legacy endpoints in one step is risky. Isolating them makes the migration incremental and prevents new generic code from importing old DTOs.

**Alternatives considered and rejected**:

- Delete legacy endpoints immediately: rejected because it would make the feature too risky.
- Keep legacy endpoints available everywhere: rejected because it would preserve domain leakage.

## R-009: Backend projection layer

**Decision**: Add explicit backend projection builders for `/api/v1`: UI config, graph, table, entities, metrics timeseries, hotspots, and diagnostics.

**Rationale**: Storage/query facts can remain domain-rich. Public API projections must be generic, stable, and UI-ready.

**Alternatives considered and rejected**:

- Make frontend adapt all legacy response shapes: rejected because it shifts backend domain coupling into frontend adapters.
- Rewrite storage first: rejected because storage refactor is not required for this feature.

## R-010: Diagnostics separation

**Decision**: Diagnostics data such as evidence and parse errors MUST NOT appear in default user-facing projections. It may remain available through diagnostics capability/endpoints.

**Rationale**: Generic UI views should not carry debug-only payloads. Diagnostics are useful but must be explicit.

**Alternatives considered and rejected**:

- Remove diagnostics facts entirely: rejected because they may be useful for debugging.
- Keep evidence in every edge/table payload: rejected because it pollutes public UI projections and API contracts.
