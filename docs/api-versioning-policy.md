# API Versioning Policy

This document defines the lifecycle of the public `/api/v1` contract.

## Lifecycle states

1. **experimental** — `/api/v1` is mounted, OpenAPI export and linting
   are in place, but no stable baseline exists. `oasdiff` produces a
   changelog and **does not fail the build**.
2. **baseline_ready** — Graph, Tables, and Metrics Dashboard have
   migrated to generated transport plus explicit domain adapters.
   A baseline artifact is committed under `openapi/baseline/current.json`.
3. **stable** — the migration gate has been promoted by a human and the
   baseline is locked. From this point on, `oasdiff breaking` is
   **blocking** for any public `/api/v1` change.

## Experimental /api/v1

While `/api/v1` is experimental:

- DTO fields may evolve.
- New endpoints may be added.
- `scripts/diff_openapi.sh` prints a non-blocking changelog.

## Baseline promotion

Promote the baseline only when the migration gate (see
`docs/frontend-api-platform-migration.md`) is satisfied:

```bash
cp openapi/openapi.json openapi/baseline/current.json
```

After promotion:

- `oasdiff breaking openapi/baseline/current.json openapi/openapi.json`
  becomes part of the CI pipeline.
- Removing an operationId, an existing endpoint, or a required field
  fails the build.
- Adding a new endpoint or optional field is allowed.

## Deprecation policy

When an endpoint or field is being retired, the implementation MUST:

1. Mark the field or operation as `deprecated: true` in the OpenAPI
   schema.
2. Emit a `Deprecation` and `Sunset` HTTP header (RFC 8594) on the
   legacy endpoint, with a sunset date at least 90 days in the future.
3. Document the migration path in `docs/frontend-api-platform-migration.md`.

The deprecation header is **distinct** from breaking-change detection
in `oasdiff`. A deprecated endpoint may still be considered
non-breaking until its sunset date passes; the breaking-change check
only fires when the contract is removed or a required field is
changed.

## Post-baseline breaking-change policy

After the first stable baseline, the CI gate fails on:

- Removed operations
- Renamed operations
- Removed required request/response fields
- Type changes for required request/response fields
- Removed enum values
- Removed HTTP status codes from existing operations
