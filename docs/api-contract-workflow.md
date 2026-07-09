# API Contract Workflow

This document describes the exact commands used to export, lint, bundle,
generate, and diff the public OpenAPI contract for the project. The steps
mirror `quickstart.md` of the `010-frontend-api-platform` feature.

## Prerequisites

- `uv` (Python 3.11+)
- `node` and `npm`
- `npx`

## Quickstart (Make)

The Makefile exposes one command per workflow step and one aggregate:

```bash
make api-contract     # lint + types + diff + boundaries
make api-lint         # export + spectral + redocly lint + bundle
make api-types        # regenerate frontend/src/api/generated/schema.d.ts
make api-diff         # non-blocking oasdiff changelog
make api-boundaries   # forbidden-identifier + import-boundary scan
```

`make api-contract` is the single command to run before pushing a change
that touches the API contract, a generic frontend view, or a backend
projection. It runs all four steps in order and fails on the first error.

## Step-by-step (manual)

```bash
# 1. Export the FastAPI app's OpenAPI schema (deterministic, sorted keys)
uv run python scripts/export_openapi.py --output openapi/openapi.json

# 2. Run all governance checks (lint + bundle + frontend type generation)
bash scripts/check_openapi.sh

# 3. Generate frontend transport types from the exported contract
cd frontend && npm run openapi:types

# 4. Generate a non-blocking changelog against the frozen baseline
bash scripts/diff_openapi.sh

# 5. Run the forbidden-identifier + import-boundary scanner
cd frontend && npm run check:frontend-boundaries
```

## Frontend TypeScript client generation

The frontend transport layer is generated from `openapi/openapi.json`
using `openapi-typescript` (writes to
`frontend/src/api/generated/schema.d.ts`). The runtime client lives in
`frontend/src/api/http.ts` and uses `openapi-fetch` bound to the
generated `paths` types. `frontend/src/api/publicApi.ts` and
`frontend/src/api/internalApi.ts` consume the typed client directly.

Both tools are listed under `frontend/package.json` `devDependencies`
(`openapi-typescript`) and `dependencies` (`openapi-fetch`) and are
pulled in by `npm install`.

### When to regenerate

Regenerate `schema.d.ts` whenever any of the following change:

- a backend response/request model in `src/ppi/server/v1_schemas.py`
- an endpoint path, query parameter, or status code in `src/ppi/server/api_v1.py`
- the `CamelModel` base (because aliases affect every property name)

The easiest way:

```bash
make api-types
```

### What is checked in

`frontend/src/api/generated/schema.d.ts` is **committed** to the repo
so reviewers see the generated client surface alongside the API change.
The checked-in file is a stub while the contract is experimental; after
the first `make api-lint` run, it is replaced by the real generated
content.

The bundled artifact `openapi/openapi.bundle.yaml` is **not** committed
(it's in `frontend/.gitignore`); it is produced for documentation and
external consumption only.

### Handling a failing typecheck after a backend change

If `tsc --noEmit` reports errors in `frontend/src/api/generated/**`
after a backend change, you almost certainly forgot to run
`make api-types`. Re-run it, then commit the regenerated
`schema.d.ts` in the same PR as the backend change.

## Outputs

| File | Committed? | Purpose |
|---|---|---|
| `openapi/openapi.json` | yes | Current exported contract. |
| `openapi/openapi.bundle.yaml` | no | Single-file bundled artifact from Redocly. |
| `openapi/baseline/current.json` | yes (after promotion) | Frozen baseline. |
| `frontend/src/api/generated/schema.d.ts` | yes | Generated transport types. |

## Governance policy

- Before the first stable baseline, `oasdiff` produces a changelog but does
  not fail the build.
- After the first stable baseline, `oasdiff breaking` becomes blocking for
  any change under `/api/v1` (see `docs/api-versioning-policy.md`).
- Spectral and Redocly enforce operationId, tags, summaries, and the
  `/api/v1` public path prefix.
- The boundary scanner (`scripts/check_frontend_boundaries.py`) fails the
  build when generic frontend code imports generated DTOs, legacy modules,
  or forbidden domain tokens.
