# Quickstart: Frontend Platform and Public API Contract Foundation

**Feature**: `010-frontend-api-platform`  
**Status**: completed

This quickstart defines validation scenarios for implementers. Run these after each implementation phase.

## 1. Prerequisites

Required tools:

```text
Python 3.11+
uv
Node.js compatible with the frontend Vite toolchain
npm or equivalent package runner
```

Project dependencies are installed with:

```bash
uv sync --extra dev
cd frontend
npm install
```

## 2. Export OpenAPI

Command:

```bash
uv run python scripts/export_openapi.py --output openapi/openapi.json
```

Expected:

- `openapi/openapi.json` exists.
- It includes `/api/v1/status`.
- It includes `/api/v1/ui/config`.
- Public `/api/v1` schemas expose `camelCase` fields.
- Public `/api/v1` operations have stable `operationId`.

## 3. Validate API Contract

Commands:

```bash
npx spectral lint openapi/openapi.json
npx redocly lint openapi/openapi.json
npx redocly bundle openapi/openapi.json -o openapi/openapi.bundle.yaml
```

Expected:

- Spectral exits successfully.
- Redocly lint exits successfully.
- `openapi/openapi.bundle.yaml` exists.

## 4. Generate Frontend Transport Types

Command:

```bash
npx openapi-typescript openapi/openapi.json -o frontend/src/api/generated/schema.d.ts
```

Expected:

- `frontend/src/api/generated/schema.d.ts` exists.
- TypeScript can find operations for `/api/v1/status`, `/api/v1/ui/config`, `/api/v1/graph`, `/api/v1/tables/{tableId}`, and metrics endpoints.

## 5. Frontend Typecheck and Build

Command:

```bash
cd frontend
npm run build
```

Expected:

- TypeScript typecheck passes.
- Vite build succeeds.
- Generic components do not import generated DTOs directly.

## 6. Backend `/api/v1` Smoke Test

Start the server using the existing project command once implemented.

Expected manual checks:

```text
GET /api/v1/status returns JSON with camelCase fields.
GET /api/v1/ui/config returns definitions arrays.
GET /api/v1/commits returns { items: [...] }.
```

For an error case, request an invalid table id:

```text
GET /api/v1/tables/does-not-exist
```

Expected error shape:

```json
{
  "error": {
    "code": "TABLE_NOT_FOUND",
    "message": "...",
    "details": {},
    "requestId": null
  }
}
```

## 7. UiConfig Fixture Test

Create a fixture with:

- one unknown metric id;
- one unknown relation type id;
- one unknown line category id;
- one unknown entity kind id;
- one graph lens;
- one table definition;
- one metric query definition.

Expected:

- `DefinitionRegistry` returns metadata for known ids.
- `DefinitionRegistry.labelForUnknown("some_new_metric")` returns a readable label.
- Generic views do not crash when ids are missing from definitions.

## 8. Graph Migration Test

Fixture requirements:

- Graph node contains `entity.id`, `entity.kind`, `entity.label`.
- Graph node does not contain required `module_name`.
- Graph edge contains `relationTypeId` and `metrics`.
- Graph edge does not contain required `breakdown.model_reuse`.

Expected:

- `EntityGraph` renders nodes and edges.
- Graph settings are populated from visual encoding definitions.
- Relation labels come from relation type definitions or fallback labels.

## 9. Tables Migration Test

Fixture requirements:

- Table response includes `columns` and `rows`.
- A row contains a drilldown action.
- Line-count values appear as explicit columns.

Expected:

- `GenericDataTable` renders unknown columns.
- Activating drilldown pushes a `DrilldownFrame`.
- No code reads `row.cells.module_name`.

## 10. Metrics Dashboard Migration Test

Fixture requirements:

- UiConfig contains two entity kinds.
- One metric supports only the first entity kind.
- One aggregation is invalid for a selected metric.
- One entity kind has no targets.

Expected:

- Changing entity kind recomputes valid metrics.
- Invalid metric is replaced by first valid metric.
- Invalid aggregation is replaced by default aggregation or first valid aggregation.
- No request is sent when no valid state exists.

## 11. Legacy Boundary Test

Run the forbidden identifier validation script after it is implemented.

Expected:

- `frontend/src/legacy/**` may contain legacy field names.
- `frontend/src/components/generic/**` may not contain legacy field names.
- `frontend/src/domain/**` may not contain legacy field names.
- `frontend/src/registry/**` may not contain legacy field names.

## 12. oasdiff Report

Before stable baseline:

```bash
scripts/diff_openapi.sh
```

Expected:

- A diff/changelog report is produced.
- The command does not fail CI before baseline.

After stable baseline:

```bash
oasdiff breaking openapi/baseline/current.json openapi/openapi.json
```

Expected:

- Breaking public `/api/v1` changes fail.
- Legacy/internal-only changes do not block public baseline checks.
