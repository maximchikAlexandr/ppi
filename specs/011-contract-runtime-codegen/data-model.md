# Data Model: Runtime Contract Code Generation and Boundary Typing

This model describes source contracts, generated artifacts, validation results, freshness results, runtime conformance, and facade rules. It is implementation-facing and intentionally concrete.

## ContractSource

Represents a human-owned or runtime-model source used for generation.

Fields:

```text
id: string
path: string
kind: "yaml" | "json_schema" | "python_model" | "openapi" | "manifest"
owner: "backend" | "frontend" | "vscode-extension" | "storage" | "runtime" | "plugins" | "docs"
phase: "P0a" | "P0b" | "P1" | "P2"
generator: string
description: string
```

Validation:

- `path` must exist, except generated-from-runtime sources that are verified by import.
- `owner` must be one of the accepted owner values.
- `description` must be non-empty for public/experimental sources.

## GeneratedArtifact

Represents one committed generated file.

Fields:

```text
path: string
sourceId: string
generator: string
phase: "P0a" | "P0b" | "P1" | "P2"
language: "python" | "typescript" | "json" | "markdown"
facadeRequired: boolean
usedBy: list["runtime" | "frontend" | "vscode-extension" | "tests" | "ci" | "docs"]
```

Validation:

- `path` must be under an approved generated output root.
- generated content must include the required header or JSON `$comment`.
- generated artifacts must be committed.

## ErrorCodeEntry

Source: `contracts/errors.yaml`.

Required fields:

```text
code: uppercase snake case string
category: client | server | runtime | workspace | contract | transport | extension | unknown
defaultMessage: string
retryable: boolean
stability: internal | experimental | public | deprecated
description: string
```

Optional transport mappings:

```text
httpStatus: integer
rpcCode: integer | string
cliExitCategory: string
webviewActionMapping: string
replacement: string
removalNote: string
```

Validation:

- duplicate `code` values are invalid.
- deprecated entries require `replacement` or `removalNote`.
- `httpStatus` is optional and may be omitted for non-HTTP errors.

## ProgressEventContract

Source: Python `ProgressEvent` union in `src/ppi/runtime/progress.py`.

Generated outputs:

```text
contracts/progress-events.schema.json
src/ppi/generated/progress_events_schema.py
frontend/src/generated/progressEvents.ts
frontend/src/generated/progressEventValidators.ts
vscode-extension/src/generated/progressEvents.ts
vscode-extension/src/generated/progressEventValidators.ts
docs/generated/progress-events.md
```

Validation:

- union must be tagged/discriminated.
- each event variant must have a stable tag.
- generated JSON Schema must include all event variants.

## WebviewProtocolContract

Source: `contracts/webview-protocol.schema.json`.

Generated outputs:

```text
frontend/src/generated/webviewProtocol.ts
frontend/src/generated/webviewProtocolValidators.ts
vscode-extension/src/generated/webviewProtocol.ts
vscode-extension/src/generated/webviewProtocolValidators.ts
docs/generated/webview-protocol.md
```

Validation:

- schema must be valid JSON Schema.
- schema must describe only messages crossing webview/extension boundary.
- generated runtime validators must use Ajv.

## GeneratedFacade

Handwritten module that stabilizes imports from generated artifacts.

Fields:

```text
path: string
generatedImports: list[string]
exports: list[string]
allowedBehavior: "export_name_normalization_only"
```

Validation:

- facade may re-export or rename generated symbols.
- facade must not perform IO.
- facade must not include business logic, service orchestration, adapters, or framework lifecycle logic.

## FreshnessReport

Result of `ppi dev check-generated`.

Fields:

```text
status: "fresh" | "stale" | "missing" | "invalid"
staleFiles: list[string]
missingFiles: list[string]
invalidSources: list[string]
remediationCommand: "uv run ppi dev generate-contracts"
```

Validation:

- stale generated docs fail freshness exactly like stale generated code.
- missing generated files fail freshness.

## RuntimeConformanceRun

Represents one Schemathesis runtime API contract run.

Fields:

```text
schemaPath: "openapi/openapi.json"
fixtureRepo: "tests/fixtures/api_contract_repo"
baseUrl: string
port: integer
maxExamples: integer
includedEndpointPattern: "/api/v1/*"
readinessPath: "/api/v1/status"
```

Validation:

- all implemented `/api/v1/*` endpoints are in scope.
- legacy endpoints are excluded from Schemathesis and readiness probing.
- parameterized endpoints must have examples/enums or deterministic seeding.

## State Transitions

### Generated artifact lifecycle

```text
source_changed -> generate -> committed_generated_artifact -> check_generated_fresh
source_changed_without_generation -> stale -> CI_failure
manual_generated_edit -> stale -> CI_failure
```

### API baseline policy

```text
experimental_baseline -> oasdiff_non_blocking
spec_011_complete -> api_diff_remains_report_only
future_separate_specification -> stable_baseline_declared -> breaking_oasdiff_blocking
```

### Import Linter rollout

```text
not_configured -> spec_011_report_only_visibility
spec_011_report_only_visibility -> future_separate_specification -> blocking_architecture_gate
```
