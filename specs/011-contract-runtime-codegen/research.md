# Research: Runtime Contract Code Generation and Boundary Typing

This document records final implementation decisions. It does not present choices to the implementer.

## Decision 1: Spec 011 does not generate REST SDKs

**Decision**: REST SDK generation remains owned by spec 010. Spec 011 only strengthens freshness and runtime conformance around committed OpenAPI artifacts.

**Rationale**: The project already has OpenAPI generation and frontend type generation. A second REST generator would create drift.

**Rejected alternatives**:

- Generate another REST client in spec 011: rejected because it duplicates spec 010.
- Generate REST types from non-REST manifests: rejected because OpenAPI is already the REST source of truth.

## Decision 2: P0a includes errors, progress events, webview protocol, docs, freshness, and mypy P0

**Decision**: P0a is limited to codegen foundation and three non-REST boundaries: error codes, progress events, and webview protocol.

**Rationale**: This gives immediate value without expanding into storage, plugins, or CLI schemas too early.

**Rejected alternatives**:

- Include DuckDB/storage schema generation: rejected and out of scope.
- Include CLI JSON schemas in P0a: rejected; kept for P1.
- Include plugin manifest in P0a/P1: rejected; kept as P2 schema/docs only.

## Decision 3: Python progress event union is source of truth

**Decision**: `src/ppi/runtime/progress.py` exposes `ProgressEvent` as the source model. JSON Schema and TypeScript artifacts are generated from it.

**Rationale**: Runtime already emits Python events. Keeping Python as source avoids manually syncing a separate schema.

**Rejected alternatives**:

- JSON Schema as progress source: rejected because it would duplicate runtime model maintenance.
- YAML manifest as progress source: rejected as too heavy for current runtime.

## Decision 4: Webview protocol source is JSON Schema

**Decision**: `contracts/webview-protocol.schema.json` is the only source of truth for webview `postMessage` protocol.

**Rationale**: Webview protocol is a cross-process JSON boundary and should not belong to React or extension implementation code.

**Rejected alternatives**:

- Frontend TypeScript as source: rejected because webview protocol does not belong to frontend alone.
- VS Code TypeBox schema as source: rejected because it makes frontend depend on extension internals.

## Decision 5: Ajv validates TypeScript runtime boundaries

**Decision**: Generated TypeScript types are paired with Ajv validators derived from JSON Schema.

**Rationale**: TypeScript types alone do not validate runtime process input. Ajv validates unknown JSON at boundaries.

**Rejected alternatives**:

- Zod as source of truth: rejected because it creates a second schema source.
- Manual type guards: rejected because they drift.

## Decision 6: All generated artifacts are committed

**Decision**: Every generated artifact from spec 011 is committed and checked for freshness.

**Rationale**: Generated files are used by runtime code, tests, CI, docs, frontend, or VS Code extension. They are deliverables, not build cache.

**Rejected alternatives**:

- Generate only at install time: rejected because it hurts reproducibility and IDE use.
- Commit only schemas/docs: rejected because runtime/test artifacts would be missing.

## Decision 7: Generated artifacts are imported through facades

**Decision**: Handwritten runtime/frontend/extension code imports small handwritten facades, not generated files directly.

**Rationale**: Facades stabilize import surface and keep generated layout from becoming a cross-project dependency.

**Rejected alternatives**:

- Import generated files everywhere: rejected because it hard-codes generated layout into business code.
- Put adapter logic in facades: rejected because facades must stay boundary-only.

## Decision 8: Schemathesis checks all implemented `/api/v1/*`

**Decision**: P0b runtime conformance checks all implemented `/api/v1/*` endpoints.

**Rationale**: Spec 10 introduced public API baseline work. Runtime conformance should protect the whole implemented v1 surface, not a manually selected subset.

**Rejected alternatives**:

- Check only safe endpoints: rejected by clarification.
- Include legacy `/api/*`: rejected because legacy is not the public contract target.

## Decision 9: Dedicated API contract fixture repository

**Decision**: Runtime conformance uses `tests/fixtures/api_contract_repo`.

**Rationale**: OpenAPI examples/enums and deterministic seeding need a stable dataset.

**Rejected alternatives**:

- Use existing mutable test fixture: rejected because it can drift for unrelated tests.
- Use external repo: rejected because CI must be deterministic.

## Decision 10: DuckDB/storage schema generation is out of scope

**Decision**: No storage schema generation, migration catalog generation, or Ibis table descriptors are implemented in spec 011.

**Rationale**: User explicitly removed it from scope. Storage codegen should be a separate specification if revisited.

**Rejected alternatives**:

- Include storage schema catalog in P0/P1/P2: rejected.

## Decision 11: Mypy blocks only P0 boundary modules

**Decision**: P0 mypy blocks `src/ppi/generated`, `src/ppi/devtools/codegen`, `src/ppi/runtime/progress.py`, `src/ppi/contracts`, and `src/ppi/devtools/cli.py`.

**Rationale**: These are new/high-risk boundary modules. Legacy query/storage typing should not block P0.

**Rejected alternatives**:

- Whole-project blocking mypy: rejected as too noisy.
- No mypy: rejected because boundary code must be typed.

## Decision 12: Import Linter is report-only for all of spec 011

**Decision**: Add Import Linter as report-only visibility in P1. It MUST remain non-blocking for all of spec 011; any blocking transition requires a separate future specification.

**Rationale**: Blocking too early can either freeze bad dependencies or create noisy failures.

**Rejected alternatives**:

- Blocking in P0: rejected as premature.
- Never use Import Linter: rejected because generated/manual boundary drift needs a guard.


## Decision 13: Worker IPC Python models are the sole source of truth

**Decision**: Generate worker IPC metadata, schemas, TypeScript types, validators, and docs exclusively from the existing `msgspec.Struct` models under `src/ppi/worker_ipc/`. Schema export failure is a validation error; no fallback schema source is allowed.

**Rationale**: The repository already exposes a msgspec-based worker boundary, and a fallback source would create dual ownership.

## Decision 14: Legacy JSON-RPC compatibility generation is required

**Decision**: Keep `ppi rpc` compatibility in P1 and generate its method catalog from `contracts/rpc-methods.yaml`. Generate constants/docs and only schemas used by existing consumers; never generate handlers.

**Rationale**: The repository documents the command as still supported even though worker IPC is primary.

## Decision 15: Typed i18n generation is excluded

**Decision**: Do not implement typed i18n key generation in spec 011.

**Rationale**: It is unrelated to the required runtime contract boundaries and would create optional work for the implementer.
