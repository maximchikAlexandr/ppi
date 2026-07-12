# Implementation Plan: Runtime Contract Code Generation and Boundary Typing

**Feature**: `011-contract-runtime-codegen`  
**Branch**: `011-contract-runtime-codegen`  
**Phase**: plan  
**Input**: `specs/011-contract-runtime-codegen/spec.md`  
**Design style**: fully decided, no implementation alternatives left for the implementer.

## 1. Summary

Implement deterministic contract-driven generation for non-REST runtime boundaries and add runtime API conformance around the existing `/api/v1` OpenAPI contract.

This plan deliberately separates four tracks:

```text
P0a: non-REST codegen foundation
P0b: runtime API conformance
P1: worker IPC generation, legacy JSON-RPC compatibility catalog, generated fixtures, and report-only import boundaries
P2: plugin manifest schema/types/docs only; typed i18n generation is out of scope
```

The implementer MUST NOT add DuckDB/storage schema generation, Ibis descriptors, VS Code command/package contribution generation, extension packaging automation, alternate REST SDK generation, or generated business logic.

## 2. Technical Context

### Current repository facts used by this plan

- Python package entrypoint is `ppi = "ppi.cli.main:cli"`.
- The backend already depends on `click`, `fastapi`, `msgspec`, `pydantic`, `Expression`, `duckdb`, and `ibis-framework[duckdb]`.
- The current root Makefile already contains an API contract workflow with `api-contract`, `api-lint`, `api-types`, `api-diff`, `api-boundaries`, and `api-freshness`.
- Current API freshness checks `openapi/openapi.json` and `frontend/src/api/generated/schema.d.ts`, but MUST be extended to also check `openapi/openapi.bundle.yaml`.
- The frontend already uses `openapi-typescript`, `openapi-fetch`, TypeScript, Vitest, and boundary-check scripts.

### Required backend dependencies

Add these to Python development dependencies using the repository's dev dependency mechanism:

```toml
schemathesis>=4.0.0
mypy>=1.10
PyYAML>=6.0.2
Jinja2>=3.1.4
jsonschema>=4.23.0
import-linter>=2.13
```

Use `uv sync --extra dev` as the primary CI/development install command. If the repository keeps dependency groups in addition to optional dependencies, the implementation MUST keep the existing CI install path working and MUST NOT require a global tool install.

### Required frontend and VS Code dependencies

Add to frontend dev dependencies:

```json
{
  "ajv": "^8.17.1",
  "json-schema-to-typescript": "^15.0.4"
}
```

If `vscode-extension/package.json` exists, add the same dependencies there. If `vscode-extension` does not exist yet, P0a MUST still generate artifacts under `vscode-extension/src/generated/` only if that package path already exists. If the path does not exist, the generator MUST skip VS Code writes with an explicit validation note and docs entry saying the VS Code target is pending. Do not create a full extension package in spec 011.

### Runtime assumptions

- Generated artifacts are committed.
- `make generate` updates generated artifacts.
- `make check-generated` detects stale generated artifacts.
- `make api-runtime-contract` starts the API against `tests/fixtures/api_contract_repo` and runs Schemathesis against committed OpenAPI.
- Legacy `/api/*` is not in runtime conformance or readiness scope. Readiness uses `/api/v1/status` only.

## 3. Constitution Check

No `memory/constitution.md` exists in this workspace. No constitution rules were checked.

The following local project constraints are treated as binding:

1. Spec 010 remains the only REST SDK generation path.
2. Spec 011 generates boundary artifacts only.
3. Generated artifacts are committed and checked for freshness.
4. DuckDB/storage schema generation is out of scope.
5. Weak implementer assumption: all file paths, command names, and tool choices are fixed in this plan.

## 4. Target File Layout

### New contract sources

```text
contracts/
  errors.yaml
  webview-protocol.schema.json
  cli/
    README.md                 # P1 only
    *.schema.json             # P1 only
```

Progress events do not use a handwritten schema source. Their source model is:

```text
src/ppi/runtime/progress.py
```

### New generated backend artifacts

```text
src/ppi/generated/
  __init__.py
  errors.py
  progress_events_schema.py
```

### New backend facade modules

```text
src/ppi/contracts/
  __init__.py
  errors.py
  progress_events.py
  validation.py
```

`src/ppi/contracts/*` are handwritten facades. Runtime code imports these facades, not generated modules directly.

### New codegen implementation

```text
src/ppi/devtools/
  __init__.py
  cli.py
  codegen/
    __init__.py
    common.py
    errors.py
    progress.py
    webview.py
    docs.py
    freshness.py
    validate.py
    render.py
    paths.py
    types.py
    rpc.py                  # P1
    cli_json.py             # P1
    fixtures.py             # P1
```

### New scripts

```text
scripts/
  check_generated_contracts.sh
  check_api_runtime_contract.sh
  check_mypy_p0.sh
```

### New generated frontend artifacts

```text
frontend/src/generated/
  errorCodes.ts
  progressEvents.ts
  progressEventValidators.ts
  webviewProtocol.ts
  webviewProtocolValidators.ts
```

### New frontend facade modules

```text
frontend/src/contracts/
  errorCodes.ts
  progressEvents.ts
  webviewProtocol.ts
```

Frontend runtime code imports `frontend/src/contracts/*`, not `frontend/src/generated/*` directly.

### New generated VS Code artifacts

If `vscode-extension/` exists:

```text
vscode-extension/src/generated/
  errorCodes.ts
  progressEvents.ts
  progressEventValidators.ts
  webviewProtocol.ts
  webviewProtocolValidators.ts
```

### New VS Code facade modules

If `vscode-extension/` exists:

```text
vscode-extension/src/contracts/
  errorCodes.ts
  progressEvents.ts
  webviewProtocol.ts
```

### Generated docs

```text
docs/generated/
  index.md
  errors.md
  progress-events.md
  webview-protocol.md
  rpc-methods.md             # P1
  cli-json.md                # P1
```

### Runtime API conformance fixture

```text
tests/fixtures/api_contract_repo/
```

This fixture is a contract fixture. It MUST NOT be casually changed by unrelated tests.

## 5. Commands and Makefile Contract

Update the root Makefile to include these targets exactly:

```makefile
.PHONY: generate validate-contracts check-generated contract-check api-runtime-contract api-contract-full mypy-p0 architecture-check ci

generate:
	uv run ppi dev generate-contracts

validate-contracts:
	uv run ppi dev validate-contracts

check-generated:
	uv run ppi dev check-generated

contract-check:
	uv run ppi dev validate-contracts
	uv run ppi dev check-generated

api-runtime-contract:
	bash scripts/check_api_runtime_contract.sh

api-contract-full: api-contract api-runtime-contract

mypy-p0:
	bash scripts/check_mypy_p0.sh

architecture-check:
	uv run lint-imports

ci: contract-check api-contract-full mypy-p0 architecture-check test
```

Keep existing spec-010 API targets. Extend existing `api-freshness` so it checks exactly these files:

```text
openapi/openapi.json
openapi/openapi.bundle.yaml
frontend/src/api/generated/schema.d.ts
```

`api-diff` is report-only for all of spec 011. A separate future specification must declare a stable baseline before it can become blocking.

## 6. P0a Design: Codegen Foundation

### 6.1 CLI command group

Add a `dev` command group under the existing Click CLI:

```text
ppi dev validate-contracts
ppi dev generate-contracts
ppi dev check-generated
```

Implementation location:

```text
src/ppi/devtools/cli.py
```

Wire the command group into the existing root CLI without changing existing user-facing commands.

### 6.2 Codegen result model

Use typed result objects in:

```text
src/ppi/devtools/codegen/types.py
```

Required models:

```text
ContractSource
GeneratedFile
GenerationPlan
ValidationIssue
ValidationReport
GenerationReport
FreshnessReport
```

Validation and generation functions MUST return explicit typed results and MUST NOT return unconstrained `Any`.

### 6.3 Path policy

Implement allowed output path policy in:

```text
src/ppi/devtools/codegen/paths.py
```

Allowed generated output roots:

```text
src/ppi/generated/
frontend/src/generated/
vscode-extension/src/generated/  
docs/generated/
contracts/progress-events.schema.json
```

Generators MUST fail validation if they would write outside these roots.

### 6.4 Header policy

All generated files MUST start with a generated header. Use this exact Python header:

```python
# Generated file. Do not edit manually.
# Source: <source>
# Generator: <generator>
```

Use this exact TypeScript/JSON/Markdown header style:

```text
// Generated file. Do not edit manually.
// Source: <source>
// Generator: <generator>
```

For JSON files, use top-level metadata fields instead of comments:

```json
{
  "$comment": "Generated file. Do not edit manually. Source: <source>. Generator: <generator>.",
  ...
}
```

For Markdown files, use:

```markdown
<!-- Generated file. Do not edit manually. Source: <source>. Generator: <generator>. -->
```

### 6.5 Error code generator

Source file:

```text
contracts/errors.yaml
```

Required manifest shape:

```yaml
version: 1
owner: backend
errors:
  - code: INVALID_REQUEST
    category: client
    defaultMessage: Invalid request.
    retryable: false
    stability: public
    description: Request payload or parameters are invalid.
    httpStatus: 400
```

Required fields per error:

```text
code
category
defaultMessage
retryable
stability
description
```

Optional fields:

```text
httpStatus
rpcCode
cliExitCategory
webviewActionMapping
replacement
removalNote
```

Validation rules:

- `code` MUST be uppercase snake case.
- `category` MUST be one of `client`, `server`, `runtime`, `workspace`, `contract`, `transport`, `extension`, `unknown`.
- `stability` MUST be one of `internal`, `experimental`, `public`, `deprecated`.
- `public` and `experimental` errors MUST have non-empty `description`.
- `deprecated` errors MUST have `replacement` or `removalNote`.
- `httpStatus` is optional and MUST NOT be required for CLI/RPC/webview-only errors.

Generated files:

```text
src/ppi/generated/errors.py
frontend/src/generated/errorCodes.ts
vscode-extension/src/generated/errorCodes.ts
docs/generated/errors.md
```

Handwritten facades:

```text
src/ppi/contracts/errors.py
frontend/src/contracts/errorCodes.ts
vscode-extension/src/contracts/errorCodes.ts
```

The facades may normalize export names and must not add logic.

### 6.6 Progress events generator

Source model:

```text
src/ppi/runtime/progress.py
```

The source MUST expose an explicit progress event union named:

```python
ProgressEvent
```

If it does not exist, P0a MUST add it. The union must include all machine-readable `ppi analyze --json` progress events.

Generated files:

```text
contracts/progress-events.schema.json
src/ppi/generated/progress_events_schema.py
frontend/src/generated/progressEvents.ts
frontend/src/generated/progressEventValidators.ts
vscode-extension/src/generated/progressEvents.ts         
vscode-extension/src/generated/progressEventValidators.ts
docs/generated/progress-events.md
```

TypeScript types are generated from JSON Schema. Runtime validators use Ajv. Zod schemas and manual type guards MUST NOT be used as source of truth.

### 6.7 Webview protocol generator

Source file:

```text
contracts/webview-protocol.schema.json
```

Generated files:

```text
frontend/src/generated/webviewProtocol.ts
frontend/src/generated/webviewProtocolValidators.ts
vscode-extension/src/generated/webviewProtocol.ts         
vscode-extension/src/generated/webviewProtocolValidators.ts
docs/generated/webview-protocol.md
```

Handwritten facades:

```text
frontend/src/contracts/webviewProtocol.ts
vscode-extension/src/contracts/webviewProtocol.ts         
```

The schema must model messages crossing the webview-extension boundary only. It must not include VS Code command contribution metadata.

### 6.8 Generated docs index

Generate:

```text
docs/generated/index.md
```

The index MUST list for each generated source:

```text
source path
owner
generator name
generated files
validation command
phase: P0a/P1/P2
```

### 6.9 Freshness algorithm

`ppi dev check-generated` MUST:

1. validate contracts;
2. regenerate into a temporary directory or deterministic in-memory map;
3. compare every generated output with the committed file;
4. fail if any file is missing, stale, or has been manually edited;
5. print the exact command: `uv run ppi dev generate-contracts`.

Do not use timestamps or current working directory in generated output.

### 6.10 P0 mypy command

Add:

```text
scripts/check_mypy_p0.sh
```

It MUST run mypy only on:

```text
src/ppi/generated
src/ppi/devtools/codegen
src/ppi/runtime/progress.py
src/ppi/contracts
src/ppi/devtools/cli.py
```

If some paths do not exist yet at the start of implementation, the script must skip missing paths with a clear line in stdout and must still fail on type errors in existing P0 paths.

## 7. P0b Design: Runtime API Conformance

### 7.1 Dependency

Add `schemathesis>=4.0.0` to dev dependencies.

### 7.2 Script

Add:

```text
scripts/check_api_runtime_contract.sh
```

The script MUST:

1. use `openapi/openapi.json` as the schema;
2. use `tests/fixtures/api_contract_repo` by default;
3. run `uv run ppi --repo "$FIXTURE_REPO" analyze --all-modules` before starting the server;
4. start `uv run ppi --repo "$FIXTURE_REPO" serve --port "$PORT"`;
5. wait for readiness using `/api/v1/status` only; failure of that endpoint fails setup;
6. verify every implemented `/api/v1/*` endpoint has fixture-compatible examples/enums or deterministic seeding when required;
7. run Schemathesis with bounded examples;
8. kill the server on exit.

Default environment variables:

```text
PPI_CONTRACT_PORT=8765
PPI_CONTRACT_FIXTURE_REPO=tests/fixtures/api_contract_repo
PPI_CONTRACT_LOG_FILE=/tmp/ppi-api-contract.log
SCHEMATHESIS_MAX_EXAMPLES=25
```

### 7.3 Endpoint scope

The script MUST include all implemented `/api/v1/*` endpoints. It MUST exclude legacy `/api/*` endpoints from Schemathesis checks.

### 7.4 Fixture repository

Create:

```text
tests/fixtures/api_contract_repo/
```

Required data properties:

- at least 3 commits;
- at least 2 Python modules/packages;
- at least 4 Python files;
- at least one file-level metric;
- at least one graph relation visible in `/api/v1/graph` if graph endpoint exists;
- stable examples for `commitId`, `entityKindId`, `metricId`, `tableId`, `lensId`, and `aggregation` when those parameters exist.

The fixture repository is contract data. Do not reuse a mutable unrelated test fixture.

## 8. P1 Design

### 8.1 JSON-RPC method manifest

Source:

```text
contracts/rpc-methods.yaml
```

Generated files:

```text
src/ppi/generated/rpc_methods.py
frontend/src/generated/rpcMethods.ts
vscode-extension/src/generated/rpcMethods.ts
docs/generated/rpc-methods.md
```

The generator produces constants and docs only. It MUST NOT generate handlers or query logic.

### 8.2 CLI JSON schemas

Source directory:

```text
contracts/cli/
```

Only stable machine-readable `--json` outputs consumed by automation, frontend, or VS Code are in scope. Human-readable commands do not need schemas.

Generated files:

```text
docs/generated/cli-json.md
frontend/src/generated/cli*.ts                  # only for consumed outputs
vscode-extension/src/generated/cli*.ts       and consumes the output
```

### 8.3 Generated fixtures

Generate deterministic fixtures under:

```text
contracts/fixtures/
```

Fixtures must be safe to commit and must be tied to their contract source.

### 8.4 Import Linter

Add:

```text
.importlinter
```

Initial contracts are non-blocking in CI. They must include:

```text
ppi.generated must not import ppi.query, ppi.server, ppi.runtime, ppi.storage
ppi.runtime, ppi.server, ppi.query, ppi.storage must not import ppi.devtools.codegen
ppi.storage must not import ppi.server
```

Make blocking only after physical package cleanup.

## 9. P2 Design

P2 MUST add plugin manifest schema/types/docs/validation helpers only. It MUST NOT implement plugin loading behavior.

Typed i18n key generation is out of scope for spec 011.

Import Linter remains report-only in spec 011. Making it blocking requires a separate future specification.

## 10. Testing Strategy

### Unit tests

Add backend unit tests for:

```text
errors.yaml validation
error code generation
progress schema generation
webview schema validation
path policy
header policy
freshness comparison
facade import behavior
```

Add frontend tests or type checks for:

```text
progress validator accepts valid fixture
progress validator rejects invalid fixture
webview validator accepts valid fixture
webview validator rejects invalid fixture
contract facades compile
```

### Contract tests

Add tests for:

```text
make validate-contracts
make generate
make check-generated
api-freshness includes openapi.bundle.yaml
```

### Runtime tests

P0b uses:

```text
make api-runtime-contract
```

It must run in CI separately from static API checks.

### Typing tests

P0 must run:

```text
make mypy-p0
```

Whole-project mypy is not a spec 011 CI gate. Only `make mypy-p0` is required and blocking.

## 11. CI Plan

### Static API contract job

Run:

```bash
uv sync --extra dev
cd frontend && npm ci
make api-contract
```

`api-freshness` must check `openapi/openapi.json`, `openapi/openapi.bundle.yaml`, and `frontend/src/api/generated/schema.d.ts`.

### Non-REST contract job

Run:

```bash
uv sync --extra dev
cd frontend && npm ci
make contract-check
make mypy-p0
```

If `vscode-extension` exists, run its install/typecheck. If it does not exist, do not create the package in this spec.

### Runtime API contract job

Run after static API contract job:

```bash
uv sync --extra dev
make api-runtime-contract
```

Node is not required in this job unless the API export step in the repository requires frontend tooling. Use committed `openapi/openapi.json`.

### Architecture visibility job

P1 only:

```bash
uv run lint-imports
```

It is always report-only and non-blocking in spec 011; its log is retained as a CI artifact.

## 12. Implementation Order

Implement in this exact order:

1. Repair/extend Makefile targets without changing existing spec-010 behavior.
2. Add `src/ppi/devtools` CLI group and empty command scaffolds.
3. Add path/header/common typed codegen utilities.
4. Add `contracts/errors.yaml` and error-code generator.
5. Add progress event union if missing and progress generator.
6. Add `contracts/webview-protocol.schema.json` and webview generator.
7. Add generated docs index generator.
8. Add handwritten facade modules.
9. Add `check-generated` freshness comparison.
10. Add P0 unit tests and `scripts/check_mypy_p0.sh`.
11. Add CI non-REST contract job.
12. Add Schemathesis dependency and `scripts/check_api_runtime_contract.sh`.
13. Add `tests/fixtures/api_contract_repo`.
14. Add OpenAPI examples/enums or deterministic seeding for every implemented `/api/v1/*` endpoint.
15. Add runtime contract CI job.
16. Add P1 JSON-RPC manifest.
17. Add P1 CLI JSON schemas.
18. Add P1 generated fixtures.
19. Add non-blocking Import Linter.
20. Add P2 plugin manifest schema/types/docs; do not add typed i18n generation.

## 13. Anti-Requirements for Implementer

Do not implement any of these:

```text
DuckDB schema generation
migration catalog generation
Ibis descriptor generation
VS Code command/package contribution generation
extension packaging automation
alternate REST SDK generator
business logic generation
handler generation
query logic generation
React component generation
plugin loading behavior
```

If a task seems to require one of these items, stop and rewrite the task to stay within this plan.
