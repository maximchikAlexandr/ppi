# Feature Specification: Frontend Platform and Public API Contract Foundation

**Feature Branch**: `010-frontend-api-platform`  
**Created**: 2026-07-08  
**Status**: Hardened Draft  
**Input**: `ppi_frontend_api_decoupling_combined.md`; project repository `https://github.com/maximchikAlexandr/ppi`

## Feature Overview

The project must introduce a frontend platform layer and a versioned API contract foundation so the user interface no longer depends on concrete Python/Odoo backend concepts such as module names, Python file count, manifest dependencies, cyclomatic fields, hardcoded relation categories, or fixed line categories.

The frontend must render abstract primitives: entities, metrics, relations, graphs, tables, filters, actions, visual encodings, pages, capabilities, and diagnostics. Concrete semantics must be owned by backend/profile/plugin metadata and delivered through explicit definitions and projections.

The API must be prepared for future public use by introducing a versioned API surface, stable generated contract artifacts, style governance, typed frontend transport generation, consistent error handling, and a clear migration path away from legacy domain-shaped endpoints.

This specification intentionally combines frontend decoupling and API foundation because doing the frontend refactor over the existing domain-shaped API would create a second migration later.

## Clarifications

### Session 2026-07-08

- Q: When should `/api/v1` be considered stable? -> A: `/api/v1` remains experimental until the main generic frontend views have migrated to the generated transport client plus explicit domain adapters; the first stable baseline is declared only after that migration point.
- Q: Which generic views are initially required before the first stable `/api/v1` baseline? -> A: Graph and Tables are required as the initial minimum migration gate.
- Q: What should happen to Metrics Dashboard before the first stable `/api/v1` baseline? -> A: Metrics Dashboard must also migrate to generic query definitions, generated transport access, and explicit domain adapters before the first stable baseline is declared.
- Q: Which endpoints should be included in generated frontend SDK generation? -> A: The generated frontend transport layer may be generated from the full OpenAPI contract, including legacy and internal endpoints; usage must still be separated so generic frontend code imports only public/generic `/api/v1` access, while legacy/internal access is isolated behind legacy or internal adapter boundaries.
- Q: Which field naming convention should `/api/v1` use? -> A: Public `/api/v1` request and response JSON MUST use `camelCase` field names. Backend implementation MAY keep internal Python model fields in `snake_case` and expose `camelCase` through explicit aliases, but the exported public API contract and generated frontend SDK MUST present `camelCase`.


## Goals

- Remove backend-domain knowledge from generic frontend components.
- Make backend/profile/plugin metadata the source of truth for labels, metrics, entity kinds, relation types, table columns, filters, visual encodings, actions, pages, and capabilities.
- Introduce a versioned API surface suitable for future public REST API evolution.
- Generate typed frontend transport DTO access from the API contract.
- Keep frontend domain models separate from generated transport DTOs.
- Allow legacy endpoints and legacy DTOs to coexist during migration without leaking into new generic components.
- Add contract governance so API drift is detected early.

## Non-Goals

- This feature does not require deleting all legacy endpoints immediately.
- This feature does not require publishing an external SDK package immediately.
- This feature does not require rewriting storage or analysis algorithms.
- This feature does not require making every existing internal endpoint public.
- This feature does not require full compliance with any external API style guide.
- This feature does not require changing the browser/IDE transport model beyond the documented API and generated client boundaries.

## User Scenarios and Testing

### User Story 1 - Generic frontend renders backend-provided domain metadata (Priority: P1)

As a user opening the dashboard, I want the UI to display metrics, entities, relation types, graph controls, and table columns based on backend-provided definitions, so that the UI works when the active profile or future plugins contribute new data types.

**Independent Test**: Start the app with a backend configuration that includes an unknown metric, unknown relation type, unknown line category, and unknown entity kind. The frontend renders usable labels, values, filters, tables, and graph items without code changes or crashes.

**Acceptance Scenarios**:

1. Given the backend provides a metric definition not previously known by the frontend, when the metric appears in a graph node, table cell, or dashboard option, then the UI displays it using its definition label and format.
2. Given the backend provides a relation type not previously known by the frontend, when it appears in a graph edge or relation table, then the UI displays a readable label from metadata or a generated fallback label.
3. Given the backend provides a new line category, when graph line display options or table line-count columns are shown, then the UI includes the category without a frontend code change.
4. Given the backend does not provide a label for an unknown identifier, when the UI renders that identifier, then the UI shows a readable fallback label and keeps the view usable.

---

### User Story 2 - Versioned API contract supports frontend migration and future public use (Priority: P1)

As a maintainer, I want new generic endpoints under a versioned API namespace, with stable contract artifacts and common error handling, so that the frontend can migrate safely and the API can later become public.

**Independent Test**: Export the API contract and verify that public/generic endpoints are versioned, have stable operation identifiers, response models, common errors, and pass API linting.

**Acceptance Scenarios**:

1. Given the API is exported, when the contract is inspected, then new public/generic endpoints are under `/api/v1`.
2. Given an endpoint returns an error, when the frontend receives it, then the error shape is consistent across public/generic endpoints.
3. Given the generated API artifact is linted, when governance checks run, then missing operation identifiers, missing tags, missing summaries, and unversioned public paths are reported.
4. Given the frontend builds, when generated transport types are used, then the frontend compiles without manually duplicated public DTO declarations.

---

### User Story 3 - Frontend uses generated transport types but keeps its own domain model (Priority: P1)

As a frontend maintainer, I want generated API transport types to be isolated from generic components, so that the UI remains stable even when transport DTOs evolve.

**Independent Test**: Modify an API DTO field in a fixture and verify that only the generated transport layer and adapter tests fail, not generic component contracts.

**Acceptance Scenarios**:

1. Given generated transport DTOs exist, when generic graph/table/dashboard components are inspected, then they do not import generated DTOs directly.
2. Given an API response is received, when it is consumed by the frontend, then it passes through an adapter before reaching domain/view models.
3. Given a legacy API response is still used, when it enters the new UI, then it is converted by a legacy adapter and legacy field names do not appear in generic components.

---

### User Story 4 - Generic graph works with entities, relations, visual encodings, and graph lenses (Priority: P2)

As a user exploring a project graph, I want graph nodes, edges, filters, labels, sizes, colors, thickness, and tooltips to be derived from metadata rather than hardcoded Python/Odoo fields.

**Independent Test**: Provide a graph lens containing non-module entities and relation types. The graph renders nodes, edges, filters, controls, tooltips, and visual encodings without using module-specific fields.

**Acceptance Scenarios**:

1. Given a graph node has entity id, kind, label, metrics, and attributes, when the graph renders it, then the UI does not require `module_name`.
2. Given a graph edge has relation type and metrics, when the graph renders it, then the UI does not require hardcoded edge breakdown categories.
3. Given a graph visual encoding definition marks a metric as node size, edge thickness, color, badge, or label, when graph controls render, then the option appears without hardcoded frontend lists.
4. Given a graph lens selects a set of entity kinds and relation types, when the user changes lenses, then the graph renders the selected projection.

---

### User Story 5 - Generic tables and drilldowns work from backend table definitions (Priority: P2)

As a user viewing tables, I want tables, columns, values, row actions, and drilldowns to be driven by backend-provided table projections, so that module/file/relation-specific tables are not hardcoded in the frontend.

**Independent Test**: Provide a table response with unfamiliar columns and a row action to drill into another table. The frontend renders the table, formats values from metadata, executes the row action, and shows the next table without knowing module/file fields.

**Acceptance Scenarios**:

1. Given a table response includes columns and rows, when the frontend renders it, then it uses the response columns rather than a separate hardcoded frontend column list.
2. Given a row includes a backend-provided drilldown action, when the user activates it, then the frontend navigates using the action metadata and does not read `module_name`.
3. Given relations are displayed as a table, when the frontend renders them, then relation data uses the same generic table renderer as other tables.
4. Given line-count columns exist, when a table renders, then those columns are explicit columns in the table projection.

---

### User Story 6 - Metrics dashboard validates queries from definitions (Priority: P2)

As a user using the metrics dashboard, I want available targets, metrics, and aggregations to update based on entity kind and metric definitions, so that unsupported combinations are impossible to submit.

**Independent Test**: Switch entity kind from one type to another where the selected target, metric, or aggregation is invalid. The UI replaces invalid selections with valid values and does not issue an invalid request.

**Acceptance Scenarios**:

1. Given the selected metric is not valid for a new entity kind, when the entity kind changes, then the metric is reset to the first valid option.
2. Given the selected aggregation is not valid for a metric, when the metric changes, then aggregation is reset to the metric's default or first valid aggregation.
3. Given no valid query state exists, when the dashboard renders, then it shows a neutral unavailable state and does not issue a request.
4. Given targets are needed for an entity kind, when the dashboard loads, then targets are requested from a target/entity catalog endpoint, not from a module table.

---

### User Story 7 - Legacy compatibility is contained and removable (Priority: P3)

As a maintainer, I want old domain-shaped endpoints and DTOs to be isolated in a legacy boundary, so that new generic frontend code cannot accidentally depend on them.

**Independent Test**: Run import-boundary and forbidden-string checks. Generic components fail the check if they import legacy modules or reference banned domain-specific identifiers.

**Acceptance Scenarios**:

1. Given legacy DTOs are still needed, when new generic components are inspected, then they do not import legacy types directly.
2. Given a forbidden domain-specific identifier appears in generic frontend code, when validation runs, then the check fails.
3. Given a legacy endpoint is replaced by a generic endpoint, when the frontend uses the new endpoint, then the legacy adapter can be removed without changing generic components.

---

### User Story 8 - API contract governance prevents accidental public API drift (Priority: P3)

As a maintainer preparing a future public API, I want linting, bundling, generated client checks, and non-blocking diff reports, so that the team can see breaking changes before API stability is promised.

**Independent Test**: Change a public endpoint path, remove a response field, or delete an operation id. Contract checks report the change. Diff reporting is non-blocking until the first stable API baseline is declared.

**Acceptance Scenarios**:

1. Given an API contract exists, when API linting runs, then style violations are reported.
2. Given a contract baseline exists, when a breaking change is introduced, then a breaking-change report is produced.
3. Given the first stable `/api/v1` baseline is declared, when breaking changes occur later, then the governance process can be made blocking.

## Functional Requirements

### A. Frontend Platform Model

- **FR-001**: The frontend MUST define generic domain primitives for metrics, entities, relations, graphs, tables, filters, visual encodings, capabilities, actions, and pages.
- **FR-002**: Generic frontend components MUST NOT treat Python/Odoo concepts as required data fields.
- **FR-003**: Generic frontend components MUST NOT read `module_name` as the universal entity identifier.
- **FR-004**: Generic frontend components MUST identify visible domain objects using an entity reference containing at least `id`, `kind`, and `label`.
- **FR-005**: The frontend MUST separate transport DTOs from domain models.
- **FR-006**: The frontend MUST convert transport DTOs into domain models through explicit adapters before generic components consume them.
- **FR-007**: Generic frontend components MUST NOT import generated transport DTOs directly.
- **FR-008**: Generic frontend components MUST NOT import legacy DTOs directly.
- **FR-009**: The frontend MUST provide a centralized definition registry for metric, entity kind, relation type, line category, table, page, capability, visual encoding, and action lookups.
- **FR-010**: The definition registry MUST provide fallback labels for unknown identifiers.
- **FR-011**: Unknown backend-provided identifiers MUST NOT crash generic frontend views.

### B. Backend-Driven UI Configuration

- **FR-012**: The backend MUST provide a UI configuration contract that is the source of truth for generic UI definitions.
- **FR-013**: The UI configuration MUST include metric definitions used by public/generic frontend views.
- **FR-014**: The UI configuration MUST include entity kind definitions used by public/generic frontend views.
- **FR-015**: The UI configuration MUST include relation type definitions used by public/generic frontend views.
- **FR-016**: The UI configuration MUST include line category definitions used by graph and table views.
- **FR-017**: The UI configuration MUST include visual encoding definitions for graph and other visual views.
- **FR-018**: The UI configuration MUST include table definitions or table catalog metadata for available public/generic tables.
- **FR-019**: The UI configuration MUST include supported capabilities for available frontend features.
- **FR-020**: The UI configuration MUST include page availability or enough capability metadata to determine page visibility.
- **FR-021**: The frontend MUST load UI configuration before rendering generic graph, table, or dashboard views.
- **FR-022**: Frontend static translation files SHOULD only translate frontend chrome and SHOULD NOT be the source of plugin/domain labels.

### C. Metrics and Values

- **FR-023**: Metrics in generic frontend models MUST be represented as metric values keyed by metric identifier or as a list of metric values.
- **FR-024**: Metrics MUST NOT be represented in generic frontend models as fixed structural fields such as `python_file_count`, `cyclomatic`, `cognitive`, or `jones`.
- **FR-025**: Metric display labels MUST come from metric definitions when available.
- **FR-026**: Metric units and formatting MUST come from metric definitions or column definitions when available.
- **FR-027**: The frontend MUST support metric distributions as generic metric distribution records.
- **FR-028**: The frontend MUST render unknown metric values using generic value rendering rules.
- **FR-029**: Runtime metric bags MAY use string keys, but generic UI code MUST interpret those keys only through definitions.

### D. Graph and Visual Views

- **FR-030**: The graph view MUST support generic entity graph nodes instead of module-shaped nodes.
- **FR-031**: The graph view MUST support generic relation graph edges instead of hardcoded edge breakdown structures.
- **FR-032**: The graph view MUST separate relation type, relation metrics, relation contributions, and visual weight metrics.
- **FR-033**: The graph view MUST support backend-provided graph lenses.
- **FR-034**: A graph lens MUST define or reference the entity kinds and relation types included in the graph projection.
- **FR-035**: Graph node size options MUST come from visual encoding definitions.
- **FR-036**: Graph edge thickness options MUST come from visual encoding definitions.
- **FR-037**: Graph color or brightness options MUST come from visual encoding definitions or metric definitions marked for visual use.
- **FR-038**: Graph filters MUST be represented as generic filter definitions.
- **FR-039**: Edge/relation type labels MUST come from relation type definitions when available.
- **FR-040**: If a relation type label is missing, the frontend MUST generate a readable fallback from the identifier.
- **FR-041**: Graph tooltips MUST render generic metric and attribute groups instead of hardcoded domain fields.
- **FR-042**: The removed graph statistics sidebar section MUST NOT remain as a required generic graph setting.

### E. Tables and Drilldowns

- **FR-043**: Generic table responses MUST include table identifier, columns, and rows.
- **FR-044**: Generic table responses MUST include actual columns for the returned data, not only references to a separate table catalog.
- **FR-045**: Generic table rows MUST include stable row identifiers.
- **FR-046**: Generic table rows MAY include row actions.
- **FR-047**: Row actions MUST be described by metadata and MUST NOT require frontend knowledge of module/file field names.
- **FR-048**: The frontend MUST support a generic drilldown stack based on row action metadata.
- **FR-049**: Relations displayed as tables MUST use the same generic table renderer as other tables.
- **FR-050**: Manifest dependencies MUST be represented as ordinary relations or table rows, not as a separate generic frontend model.
- **FR-051**: Line-count table columns MUST be explicit columns in table projections.
- **FR-052**: The frontend MUST NOT load all file rows solely to perform a module-specific client-side drilldown.
- **FR-053**: Table values MUST be rendered through generic value renderers based on column or metric metadata.

### F. Dashboard and Query Validation

- **FR-054**: Dashboard query controls MUST be driven by metric, entity kind, target, aggregation, and query definitions.
- **FR-055**: Dashboard query controls MUST NOT depend on hardcoded `module` and `file` levels as the only possible scopes.
- **FR-056**: The API MUST provide a way to list valid targets for an entity kind and snapshot/time point.
- **FR-057**: The frontend MUST recompute valid metrics when selected entity kind changes.
- **FR-058**: The frontend MUST recompute valid targets when selected entity kind or snapshot/time point changes.
- **FR-059**: The frontend MUST recompute valid aggregations when selected metric changes.
- **FR-060**: The frontend MUST prevent requests while dashboard query state is invalid.
- **FR-061**: If the selected metric, target, or aggregation becomes invalid, the frontend MUST replace it with a valid value when one exists.
- **FR-062**: If no valid value exists, the frontend MUST display a neutral unavailable state.

### G. API Versioning and Public Contract Foundation

- **FR-063**: New public/generic REST endpoints MUST use a versioned namespace.
- **FR-064**: The initial versioned namespace MUST be `/api/v1`.
- **FR-065**: Legacy unversioned endpoints MAY remain during migration.
- **FR-066**: Legacy unversioned endpoints MUST NOT be treated as the future public API foundation.
- **FR-067**: Public/generic API endpoints MUST have stable operation identifiers.
- **FR-068**: Public/generic API endpoints MUST have explicit response models.
- **FR-069**: Public/generic API endpoints MUST have stable tags and summaries in the API contract.
- **FR-070**: Public/generic API endpoints MUST use a common error response shape.
- **FR-071**: Public/generic API endpoints MUST use consistent request parameter naming.
- **FR-072**: The API field naming convention MUST be consistent across `/api/v1`.
- **FR-073**: Public `/api/v1` request and response JSON fields MUST use `camelCase`.
- **FR-074**: Backend implementation models MAY use internal `snake_case` field names, but the exported public API contract and generated frontend SDK MUST expose `camelCase` for `/api/v1` fields.
- **FR-075**: Internal, experimental, and public endpoints MUST be distinguishable by path, documentation metadata, or contract generation scope.
- **FR-076**: The generated frontend transport layer MAY be generated from the full API contract, including public, legacy, and internal endpoints.
- **FR-077**: Generated access to public/generic `/api/v1`, legacy, and internal endpoints MUST be partitioned by explicit entrypoints, namespaces, or adapter boundaries.
- **FR-078**: Generic frontend platform code MUST import only the public/generic `/api/v1` transport entrypoint or domain adapters built on that entrypoint.
- **FR-079**: Legacy and internal generated endpoints MUST NOT be exposed as the default frontend API client for new generic components.

### H. OpenAPI Contract Artifacts and Governance

- **FR-080**: The project MUST be able to export the API contract as a stable artifact.
- **FR-081**: The exported API contract MUST include the public/generic `/api/v1` endpoints.
- **FR-082**: The exported API contract MUST be usable by frontend transport type generation.
- **FR-083**: The exported API contract MUST be linted for the project API style rules.
- **FR-084**: API linting MUST detect missing operation identifiers on public/generic endpoints.
- **FR-085**: API linting MUST detect missing tags or summaries on public/generic endpoints.
- **FR-086**: API linting MUST detect unversioned endpoints that are marked public/generic.
- **FR-087**: API contract bundling or validation MUST produce a publishable contract artifact.
- **FR-088**: API diff reporting MUST be available before the API is declared stable.
- **FR-089**: API diff reporting MAY be non-blocking while `/api/v1` is experimental.
- **FR-090**: `/api/v1` MUST remain experimental until Graph and Tables use generated transport access plus explicit domain adapters for their generic data flows.
- **FR-091**: `/api/v1` MUST also remain experimental until Metrics Dashboard uses generic query definitions, generated transport access, and explicit domain adapters.
- **FR-092**: The first stable `/api/v1` baseline MUST NOT be declared while Graph, Tables, or Metrics Dashboard still depend on legacy/domain-shaped public contracts for their primary data flows. FR-092 is the consolidated normative gate; FR-090 and FR-091 state the per-view conditions that FR-092 aggregates.
- **FR-093**: After the first stable `/api/v1` baseline is declared, breaking-change detection SHOULD become blocking for public endpoints.
- **FR-094**: The project MUST define a deprecation policy before declaring `/api/v1` stable.

### I. Generated Frontend Transport Client

- **FR-095**: Frontend transport DTO types for API calls MUST be generated from the exported API contract when those calls are part of the generated transport layer.
- **FR-096**: Generated transport usage MUST preserve the separation between public/generic `/api/v1`, legacy, and internal calls.
- **FR-097**: The generated transport client MUST be used for new `/api/v1` frontend calls.
- **FR-098**: Generated transport DTOs MUST NOT be treated as frontend domain models.
- **FR-099**: The frontend MUST maintain explicit adapters from generated transport DTOs to frontend domain models.
- **FR-100**: Manual public DTO declarations in the frontend MUST be removed or marked legacy after generated transport DTOs are introduced.
- **FR-101**: Runtime validation schemas MAY remain for legacy endpoints and bridge boundaries, but MUST NOT duplicate the public API source of truth unnecessarily.

### J. Legacy Boundary and Cleanup

- **FR-102**: Legacy frontend adapters MUST isolate old Python/Odoo-shaped DTOs from generic components.
- **FR-103**: Legacy code MUST be physically or logically separated from generic frontend platform code.
- **FR-104**: The project MUST define forbidden domain-specific identifiers for generic frontend code.
- **FR-105**: Generic frontend code MUST fail validation if it directly references forbidden domain-specific identifiers.
- **FR-106**: Generic frontend code MUST fail validation if it imports legacy DTOs or Odoo/Python profile files directly.
- **FR-107**: Components with domain-specific names MAY exist temporarily as wrappers, but their generic replacements MUST be introduced.
- **FR-108**: Legacy wrappers MUST be removable without changing generic components once backend generic projections are complete.

### K. Backend Projection Responsibility

- **FR-109**: Backend query responses for generic endpoints MUST be projections designed for public/generic UI use, not raw storage facts.
- **FR-110**: The backend MUST distinguish canonical analysis records from UI graph projections, table projections, dashboard projections, treemap projections, and diagnostics projections.
- **FR-111**: User-facing projections MUST exclude diagnostics-only data unless the requested capability is diagnostics.
- **FR-112**: Evidence, parse errors, and technical failures MUST NOT be included in default user-facing projections unless explicitly exposed as diagnostics.
- **FR-113**: The backend MAY continue storing useful analytical facts even when they are no longer shown in default UI projections.

## Edge Cases

- **EC-001**: Backend provides a metric value with no matching metric definition; the UI renders a readable fallback label and generic value.
- **EC-002**: Backend provides a relation type with no label; the UI generates a readable fallback label from the identifier.
- **EC-003**: Backend provides an unknown entity kind; the UI uses generic entity rendering and does not crash.
- **EC-004**: Backend provides a table column type unknown to the frontend; the UI renders the value as text or generic JSON-safe output.
- **EC-005**: Backend provides a visual encoding role unknown to the frontend; the UI ignores that role and records a development warning when applicable.
- **EC-006**: UI configuration fails to load; generic views display a blocking unavailable state instead of rendering from hardcoded defaults.
- **EC-007**: Dashboard has no valid metrics for the selected entity kind; the dashboard shows an unavailable state and does not request data.
- **EC-008**: Dashboard target list for an entity kind is empty; target-dependent queries are disabled.
- **EC-009**: Table response has zero rows but valid columns; the table shows an empty state with visible column headers.
- **EC-010**: Table response has row actions unavailable for a row; only available actions are shown.
- **EC-011**: Legacy API response contains old domain fields; only legacy adapters may read those fields.
- **EC-012**: Generated transport types change after OpenAPI export; frontend adapters fail type checking before generic components are affected.
- **EC-013**: Public endpoint is renamed or removed while `/api/v1` is experimental; diff report records it but does not block until stable baseline is declared.
- **EC-014**: Public endpoint is renamed or removed after stable baseline; breaking-change detection blocks or requires explicit migration/versioning decision.
- **EC-015**: Internal or legacy endpoint exists in the full generated transport layer; generic frontend code cannot import it except through an explicit legacy/internal adapter boundary.
- **EC-016**: Graph or Tables still depend on legacy/domain-shaped public contracts; `/api/v1` cannot be declared stable.
- **EC-017**: Metrics Dashboard still depends on legacy levels, hardcoded metric IDs, or domain-shaped target lookup; `/api/v1` cannot be declared stable.
- **EC-018**: Full OpenAPI generation exposes an old domain-shaped endpoint; import-boundary checks or adapter tests catch any attempt to use it directly from generic components.

## Key Entities

- **Metric Definition**: Metadata describing a metric identifier, label, value type, unit, format, scope, supported aggregations, supported entity kinds, supported views, and ownership.
- **Metric Value**: Runtime value associated with a metric identifier and optional aggregation.
- **Metric Distribution**: Aggregated metric statistics for one metric, such as count, mean, median, p95, and max.
- **Entity Kind Definition**: Metadata describing a category of entity that the UI can render.
- **Entity Reference**: Stable reference to a concrete entity with id, kind, and label.
- **Relation Type Definition**: Metadata describing a kind of relationship between entities.
- **Relation Record**: Canonical relationship between entities before projection into graph or table views.
- **Graph Lens Definition**: Metadata describing which entity kinds and relation types a graph projection includes.
- **Graph Projection**: UI-ready graph response containing generic nodes and edges.
- **Table Definition**: Catalog metadata for an available table.
- **Table Projection**: UI-ready table response containing columns, rows, and row actions.
- **Table Column Definition**: Metadata describing a table column id, label, value type, formatting, sorting, width, and metric link when applicable.
- **Table Row Action**: Backend-provided row action such as drilldown, navigate, or select.
- **Drilldown Frame**: Frontend state frame representing a table, title, and query parameters in a drilldown stack.
- **Filter Definition**: Metadata describing a filter target, kind, options, and default value.
- **Visual Encoding Definition**: Metadata describing how a metric or attribute can control size, color, thickness, badge, label, or other visual roles.
- **Capability Definition**: Metadata describing a feature available in the current profile/API, such as graph, tables, dashboard, treemap, timelapse, or diagnostics.
- **Page Definition**: Metadata describing page availability and required capabilities.
- **Profile Definition**: Metadata describing the active profile and contributing plugins.
- **Plugin Contribution Definition**: Metadata describing contributed metrics, entities, relations, tables, graph lenses, visual encodings, and queries.
- **API Contract Artifact**: Exported machine-readable API description used for linting, documentation, diffing, and transport type generation.
- **Generated Transport DTO**: Type generated from the API contract for HTTP transport boundaries.
- **Frontend Domain Model**: Hand-written generic frontend model consumed by components.
- **Legacy Adapter**: Migration boundary that converts old domain-shaped DTOs into generic domain models.

## Success Criteria

- **SC-001**: A new backend-provided metric appears in a graph, table, or dashboard without editing a React component.
- **SC-002**: A new backend-provided relation type appears in graph filters and relation tables without editing a React component.
- **SC-003**: A new backend-provided line category appears in graph controls or table columns without editing a React component.
- **SC-004**: Generic graph rendering works for at least one non-module entity kind in a test fixture.
- **SC-005**: Generic table rendering works for a table whose columns are unknown at frontend compile time.
- **SC-006**: Dashboard does not issue invalid requests when entity kind, target, metric, or aggregation selections become incompatible.
- **SC-007**: New public/generic endpoints are available under `/api/v1`.
- **SC-008**: Exported API contract includes `/api/v1` public/generic endpoints.
- **SC-009**: API linting reports missing operation identifiers, tags, summaries, or unversioned public paths.
- **SC-010**: Frontend transport types are generated from the exported API contract, and public/generic `/api/v1`, legacy, and internal access are separated by explicit entrypoints or adapters.
- **SC-011**: Generated frontend transport types for `/api/v1` expose `camelCase` field names matching the public API contract.
- **SC-012**: Generic frontend components do not import generated transport DTOs directly.
- **SC-013**: Generic frontend components do not import legacy DTOs directly.
- **SC-014**: Forbidden domain-specific identifiers are absent from generic frontend code.
- **SC-015**: Legacy domain-shaped endpoints can continue working through legacy adapters during migration.
- **SC-016**: A contract diff report can be produced between two API contract versions.
- **SC-017**: The first stable `/api/v1` baseline is not declared until Graph, Tables, and Metrics Dashboard use generated transport access plus explicit domain adapters for their primary data flows.
- **SC-018**: Default user-facing projections do not include diagnostics-only evidence or parse-error details.
- **SC-019**: The frontend can render unknown identifiers with fallback labels and without runtime crashes.
- **SC-020**: Removing a legacy wrapper after migration does not require changes to generic components.
- **SC-021**: Generic frontend components cannot import generated legacy/internal endpoint access directly.

## Assumptions

- **A-001**: Existing legacy endpoints may remain during migration.
- **A-002**: New generic/public endpoints will be introduced under `/api/v1`.
- **A-003**: `camelCase` is the public field naming convention for `/api/v1` request and response JSON. Internal Python models may keep `snake_case` fields when explicit aliases preserve the public `camelCase` contract.
- **A-004**: Generated transport types are for API transport only and are not the frontend domain model.
- **A-005**: The frontend domain model remains hand-written because it represents rendering primitives, not transport payloads.
- **A-006**: A first API baseline may be declared only after Graph, Tables, and Metrics Dashboard have migrated to generated transport access plus explicit domain adapters.
- **A-007**: API diff checks may be non-blocking before the first stable baseline.
- **A-008**: API diff checks should become blocking for public endpoints after the stable baseline.
- **A-009**: API governance tools are implementation choices; the product requirement is contract linting, bundling/validation, diffing, and typed transport generation.
- **A-010**: Diagnostics data may remain available outside default user-facing projections.
- **A-011**: Future plugins may contribute entity kinds, metrics, relation types, graph lenses, tables, visual encodings, filters, and queries.
- **A-012**: Frontend static localization is for application chrome; plugin/domain labels come from definitions.
- **A-013**: Full OpenAPI-based transport generation may include legacy/internal endpoints, but generated output is not automatically a public SDK surface.

## Out of Scope for This Specification

- Full removal of all legacy endpoints.
- External SDK package publishing.
- API authentication and authorization model.
- Remote multi-user deployment security model.
- Full public documentation site.
- Full compliance with Google AIP or Zalando REST Guidelines.
- Protobuf/gRPC API surface.
- Rewriting analysis storage schema.

## Documentation Notes

- API governance and SDK generation details belong in `plan.md` and later tasks, not in this specification.
- This specification requires contract governance capabilities but does not mandate a single external tool in the functional requirements.
- The implementation plan may choose concrete tools such as OpenAPI export, API style linting, API diffing, documentation bundling, and TypeScript transport generation.

## Implementation Hardening Addendum

This section removes ambiguity for implementation by weaker coding models. It is normative for this feature unless a later accepted clarification supersedes it.

### Mandatory default decisions

- **HD-001**: Treat this feature as an additive migration. Do not delete, rename, or break existing legacy routes until all Graph, Tables, and Metrics Dashboard migration gates pass.
- **HD-002**: `/api/v1` public DTO field names are `camelCase` only. If a Pydantic model uses Python `snake_case`, it must define aliases and must export OpenAPI properties as `camelCase`.
- **HD-003**: The generated frontend transport may include legacy/internal operations, but generic frontend code must import only `frontend/src/api/publicApi.ts` or domain adapters exposed by that facade.
- **HD-004**: A generic component may display `attributes` and metric ids, but it must not branch on known PPI/Odoo field names such as `module_name`, `manifest_depends`, or `python_file_count`.
- **HD-005**: Every new `/api/v1` handler must delegate data shaping to `src/ppi/query/projections.py` or a same-layer projection helper; handlers must not duplicate frontend-specific transformation logic.
- **HD-006**: Every adapter must be a pure function with deterministic output for the same input DTO and definition registry.
- **HD-007**: Missing optional backend data must degrade to empty arrays, `null`, unavailable states, or fallback labels as specified here; it must not throw in generic render paths.
- **HD-008**: Tests and fixture files may contain legacy field names only when their filename or parent directory clearly marks them as legacy or boundary tests.
- **HD-009**: Public/generic endpoint additions after this spec must follow the same `/api/v1`, `camelCase`, `operationId`, tag, summary, and `ErrorResponse` rules.
- **HD-010**: Stable baseline promotion is a manual repository decision after validation passes; no task may automatically mark `/api/v1` stable.

### Deterministic fallback behavior

- Unknown id label fallback: split on `.`, `_`, `-`, and `/`; drop empty segments; capitalize each segment; join with spaces. Example: `manifest_depends` -> `Manifest Depends`.
- Empty or whitespace-only label fallback: use the transformed id; if id is also empty, use `Unknown`.
- Unknown metric value format: render numbers with locale-aware decimal formatting, booleans as `Yes`/`No`, null or undefined as an em dash, and strings as escaped text.
- Unknown visual encoding role: ignore it in production rendering and emit only a development warning.
- Unknown table column value type: treat as `json` and render a compact escaped JSON string.

### Required initial `/api/v1` projection defaults

- If `commitId` is omitted, endpoints that require a snapshot use the latest available commit by repository order.
- If the history store is absent, read endpoints return an `ErrorResponse` with code `STORE_NOT_READY`, not a legacy-shaped error.
- `limit` defaults must be applied server-side and reflected in OpenAPI.
- All list responses return `{ "items": [] }` rather than a bare array.
- Empty graph, table, timeseries, and hotspot responses are valid responses when inputs are valid but no data exists.

### Definition ownership

- Backend/profile/plugin metadata owns all labels and display semantics for domain concepts.
- Frontend translation files own only shell/chrome labels such as navigation text, loading messages, empty states, and generic error messages.
- Legacy Odoo/Python labels must live in `frontend/src/legacy/legacyOdooLabels.ts` or backend profile metadata, never in generic renderer code.

### Adapter boundary acceptance

An implementation is acceptable only when these imports are true:

- `frontend/src/components/generic/**` imports no generated DTOs and no legacy modules.
- `frontend/src/domain/**` imports no React, Mantine, generated DTOs, or legacy modules.
- `frontend/src/pages/**` may call `publicApi` after migration but may not inspect generated DTO shapes directly.
- `frontend/src/api/adapters/**` may import generated DTOs and domain types, and may import legacy DTOs only in files whose names begin with `legacy` or explicitly document transition behavior.
