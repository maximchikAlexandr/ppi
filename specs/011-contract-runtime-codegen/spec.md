# Feature Specification: Runtime Contract Code Generation and Boundary Typing

**Feature Branch**: `011-contract-runtime-codegen`  
**Created**: 2026-07-09  
**Status**: Draft  
**Input**: Uploaded consolidated improvement document; project repository `https://github.com/maximchikAlexandr/ppi`  

## Feature Overview

This feature makes runtime contracts, non-REST process boundaries, generated artifacts, and high-risk typed boundaries explicit, deterministic, and continuously checked.

The project already has or is expected to have spec 010 implemented: versioned REST API contract, OpenAPI artifact export, frontend transport type generation, frontend REST adapters, and public API governance. This feature builds on that foundation and MUST NOT create a second REST SDK generation path.

The scope of this feature is the remaining contract boundaries:

- committed API contract freshness across all REST-generated artifacts;
- runtime API conformance against the committed API contract;
- non-REST runtime boundary code generation;
- CLI JSON and progress event schemas;
- shared error codes;
- VS Code/webview protocol artifacts;
- deterministic generated docs and fixtures;
- typed Python pipeline, query, storage, JSON, and msgspec boundaries;
- developer commands and CI gates that prevent stale generated artifacts;
- report-only architecture import boundaries for the current package layout.

The guiding rule is strict: generation is limited to boundary code, schemas, constants, docs, fixtures, and typed wrappers. Generators MUST NOT produce business logic, analysis algorithms, storage query semantics, React components, or plugin implementations.

## Goals

- Treat API and runtime contracts as committed, versioned, checkable artifacts.
- Add a runtime API conformance gate that checks the running API against the committed API contract.
- Add deterministic non-REST code generation for runtime boundaries that are not handled by spec 010.
- Add a thin developer command surface for generation, validation, and freshness checks.
- Strengthen Python typing at process, query, storage, JSON, and pipeline boundaries.
- Report invalid import directions between generated code, devtools, runtime code, storage code, and server/API layers without blocking spec 011 CI.
- Keep implementation incremental so the first iteration adds useful gates without overloading the project with unnecessary generators.

## Non-Goals

- This feature MUST NOT replace or duplicate the REST SDK generation from spec 010.
- This feature MUST NOT create an alternative REST client generator.
- This feature MUST NOT generate analysis business logic.
- This feature MUST NOT generate storage query decisions or domain-specific analytics.
- This feature MUST NOT require immediate full API fuzzing across every endpoint.
- This feature MUST NOT require immediate strict typing for the entire backend codebase.
- This feature MUST NOT require immediate blocking import-linter enforcement before package boundaries are physically separated.
- This feature MUST NOT implement a full plugin loading system.
- This feature MUST NOT publish an external SDK package.

## Dependencies and Ordering

- **D-001**: Spec 010 MUST be implemented or in progress before this feature is started.
- **D-002**: REST/OpenAPI transport generation remains owned by spec 010.
- **D-003**: This feature MUST strengthen freshness checks for the three spec 010 artifacts named in FR-031–FR-033 and MUST NOT redefine the REST client generation approach.
- **D-004**: Runtime API conformance checks MUST use the committed API contract artifact produced by spec 010.
- **D-005**: Non-REST code generation MUST use separate source contracts and MUST NOT infer contracts from generated REST SDK files.

---

## User Scenarios and Testing

### User Story 1 — Developer validates all contract sources

As a maintainer, I can run one command that validates every source contract before generation, so invalid YAML, JSON Schema, duplicate IDs, invalid schema files, or unsafe generated paths fail early.

**Acceptance Scenarios**:

1. Given a valid contract source set, when contract validation runs, then the command exits successfully and reports validated sources.
2. Given a duplicate error code, when contract validation runs, then the command fails and identifies the duplicate ID.
3. Given a generated output path outside the approved generated directories, when contract validation runs, then the command fails before writing files.

### User Story 2 — Developer regenerates deterministic boundary artifacts

As a maintainer, I can run one generation command that regenerates all configured non-REST generated artifacts, so Python, TypeScript, docs, and fixtures do not drift from contract sources.

**Acceptance Scenarios**:

1. Given unchanged source contracts, when generation runs twice, then the generated files are byte-for-byte identical.
2. Given `contracts/errors.yaml` changes, when generation runs, then Python error codes, frontend error codes, VS Code error codes, and error docs are updated together.
3. Given progress event contracts change, when generation runs, then progress JSON Schema, TypeScript event unions, VS Code event types, and progress docs are updated together.

### User Story 3 — CI detects stale generated artifacts

As a maintainer, CI fails when committed generated artifacts are stale, so contract changes cannot merge without regenerated code and docs.

**Acceptance Scenarios**:

1. Given a contract source changes but generated files are not updated, when freshness check runs, then CI fails with a clear remediation message.
2. Given generated files are current, when freshness check runs, then CI passes.
3. Given a developer edits a generated file manually without changing its source contract, when freshness check runs, then CI fails and instructs the developer to regenerate.

### User Story 4 — Runtime API matches the committed OpenAPI contract

As a maintainer, I can run a runtime API conformance check against a prepared fixture repository, so the running API cannot silently drift from the committed OpenAPI contract.

**Acceptance Scenarios**:

1. Given a prepared fixture repository and committed API contract, when runtime conformance runs, then the API server starts, readiness is verified, and schema-based requests are executed.
2. Given a runtime response shape differs from the committed API contract, when runtime conformance runs, then the command fails.
3. Given the fixture repository is missing, when runtime conformance runs, then the command fails with a message explaining how to set the fixture path.

### User Story 5 — VS Code extension consumes typed progress events

As a VS Code extension developer, I consume `ppi analyze --json` progress events through generated types and runtime validators, so process stream parsing is safe and synchronized with backend event definitions.

**Acceptance Scenarios**:

1. Given a valid progress event line, when the extension decoder reads it, then it accepts the event and exposes a typed union.
2. Given an unknown or malformed progress event line, when the extension decoder reads it, then it rejects the event with a structured error.
3. Given progress event definitions change, when generation runs, then backend schema, frontend type, VS Code type, and docs change together.

### User Story 6 — Shared error codes do not drift

As a backend, frontend, or extension developer, I use one generated error code catalog, so error handling does not diverge between Python, browser UI, and VS Code extension.

**Acceptance Scenarios**:

1. Given a new error is added to the manifest, when generation runs, then Python and TypeScript code can reference it through generated types/constants.
2. Given a public error lacks a description, when contract validation runs, then validation fails.
3. Given a deprecated error lacks replacement or removal notes, when contract validation runs, then validation fails.

### User Story 7 — Python boundary typing is strict at designated boundaries

As a maintainer, I can gradually enforce stronger typing at dangerous boundaries, so broad `Any`, `object`, raw JSON dictionaries, and untyped `Result` values are reduced without requiring immediate strict typing everywhere.

**Acceptance Scenarios**:

1. Given P0 boundary zones are configured, when type checking runs, then those zones are checked with explicit aliases and typed unions.
2. Given a query boundary returns untyped `Any`, when the configured type check scope includes that boundary, then the issue is reported.
3. Given non-P0 legacy code still has unresolved typing issues, when the first phase runs, then it does not block unrelated implementation unless the zone is included in the blocking scope.

### User Story 8 — Architecture import boundaries are visible without blocking this feature

As a maintainer, I run report-only import boundary checks against the current package layout, so generated code importing business logic and runtime code importing devtools generators are always reported.

**Acceptance Scenarios**:

1. Given generated code imports query/server/runtime/storage modules, when architecture check runs, then it fails.
2. Given runtime production code imports code generation devtools, when architecture check runs, then it fails.
3. Given the spec 011 CI pipeline, when Import Linter runs, then it always reports violations but never fails the spec 011 CI job; making it blocking requires a separate future specification.

---

## Functional Requirements

### A. Contract Scope and Source Ownership

- **FR-001**: The project MUST distinguish REST/OpenAPI generated artifacts from non-REST/runtime-boundary generated artifacts.
- **FR-002**: REST API transport generation MUST remain the single REST SDK path defined by spec 010.
- **FR-003**: Non-REST generators MUST NOT produce REST clients.
- **FR-004**: Every generated file MUST have exactly one declared source contract or source model.
- **FR-005**: Every source contract MUST declare an owner area before it is used for generation.
- **FR-006**: Accepted owner areas MUST be limited to backend, frontend, vscode-extension, storage, runtime, plugins, and docs.
- **FR-007**: Public or experimental contract entries MUST include descriptions.
- **FR-008**: Deprecated contract entries MUST include replacement or removal notes.
- **FR-009**: Contract validation MUST reject duplicate IDs across each contract namespace.
- **FR-010**: Contract validation MUST reject generated output paths outside approved generated artifact directories.

### B. Generated Artifact Rules

- **FR-011**: Every generated file MUST include a header stating that it is generated and must not be manually edited.
- **FR-012**: Every generated file header MUST identify the source contract path or source model.
- **FR-013**: Every generated file header MUST identify the generator name.
- **FR-014**: Generators MUST produce deterministic output.
- **FR-015**: Generated output MUST NOT include timestamps.
- **FR-016**: Generated output MUST NOT include machine-specific absolute paths.
- **FR-017**: Generated collections MUST be sorted deterministically.
- **FR-018**: Generation MUST be safe to run repeatedly without changing files when sources are unchanged.
- **FR-019**: Generated files MUST NOT contain handwritten business logic.
- **FR-020**: Generated files MUST NOT contain domain analysis algorithms.

### C. Developer Commands

- **FR-021**: The project MUST provide a root-level generation command for non-REST contract artifacts.
- **FR-022**: The project MUST provide a root-level validation command for contract sources.
- **FR-023**: The project MUST provide a root-level freshness check command for generated artifacts.
- **FR-024**: The project MUST provide a root-level combined contract check command that validates sources and checks generated freshness.
- **FR-025**: Root command entrypoints MUST be thin wrappers over Python or Node commands.
- **FR-026**: Root command entrypoints MUST NOT contain business logic.
- **FR-027**: The generation command MUST regenerate every configured non-REST generated artifact.
- **FR-028**: The freshness command MUST exit non-zero when committed generated artifacts are stale.
- **FR-029**: The freshness command MUST provide a clear remediation message naming the command to run.
- **FR-030**: The validation command MUST validate all configured contract sources without writing generated files.

### D. Static API Artifact Freshness

- **FR-031**: The existing API contract freshness check MUST verify the committed OpenAPI JSON artifact.
- **FR-032**: The existing API contract freshness check MUST verify the committed bundled OpenAPI artifact.
- **FR-033**: The existing API contract freshness check MUST verify the committed generated frontend API type artifact.
- **FR-034**: Static API freshness failures MUST identify every stale artifact that must be regenerated.
- **FR-035**: Static API freshness checks MUST remain separate from runtime API conformance checks.
- **FR-036**: API diff reporting MUST remain report-only and non-blocking throughout spec 011; changing it to blocking requires a separate specification that declares the stable API baseline.

### E. Runtime API Conformance

- **FR-037**: The project MUST provide a runtime API conformance command that starts the API against a fixture repository and checks runtime behavior against the committed API contract.
- **FR-038**: The runtime API conformance command MUST prepare or verify analyzed fixture data before starting the server.
- **FR-039**: The runtime API conformance command MUST verify server readiness before running schema-based checks.
- **FR-040**: The runtime API conformance command MUST fail clearly if the committed API contract artifact is missing.
- **FR-041**: The runtime API conformance command MUST fail clearly if the fixture repository is missing.
- **FR-042**: The runtime API conformance command MUST support configurable port, base URL, fixture repository path, log path, and max generated examples.
- **FR-043**: The first runtime conformance phase MUST use a low bounded generated-example count suitable for pull request CI.
- **FR-044**: Runtime conformance MUST include all implemented `/api/v1/*` endpoints in the first runtime conformance scope, while excluding legacy `/api/*` endpoints from Schemathesis checks.
- **FR-045**: Runtime conformance MUST require fixture-compatible OpenAPI examples/enums or deterministic seeding for every `/api/v1` endpoint that has domain parameters.
- **FR-046**: Runtime API conformance MUST be separate from static API contract generation and linting.

### F. Stable Fixture Repository

- **FR-047**: Runtime API conformance MUST use a stable fixture repository.
- **FR-048**: The fixture repository MUST include enough data to exercise status, commits, UI config, graph, metrics, and table endpoints that are included in the first runtime conformance scope.
- **FR-049**: The fixture repository path MUST be configurable for local development and CI.
- **FR-050**: OpenAPI examples used for runtime conformance MUST match data that exists in the fixture repository.
- **FR-051**: If examples or deterministic seeding are missing for a domain parameter needed by runtime conformance, runtime conformance setup MUST fail before Schemathesis runs.

### G. Error Code Catalog

- **FR-052**: The project MUST define a single error code source contract.
- **FR-053**: Error code generation MUST produce Python error code artifacts.
- **FR-054**: Error code generation MUST produce frontend TypeScript error code artifacts.
- **FR-055**: Error code generation MUST produce VS Code extension TypeScript error code artifacts.
- **FR-056**: Error code generation MUST produce generated error documentation.
- **FR-057**: Error entries MUST include code, category, default message, retryability, stability, and description.
- **FR-058**: Public error entries MUST include an HTTP status or explicit statement that they are non-HTTP errors.
- **FR-059**: Generated error code artifacts MUST preserve the exact error code values from the source contract.

### H. Progress Event Contract

- **FR-060**: Progress event source definitions MUST remain owned by the backend runtime event model.
- **FR-061**: Progress event generation MUST produce a JSON Schema artifact.
- **FR-062**: Progress event generation MUST produce frontend TypeScript types.
- **FR-063**: Progress event generation MUST produce VS Code extension TypeScript types.
- **FR-064**: Progress event generation MUST produce generated progress event documentation.
- **FR-065**: Progress event runtime consumers MUST validate or decode events through generated or generated-schema-derived artifacts.
- **FR-066**: Progress events MUST be represented as a tagged union at encode/decode boundaries.
- **FR-067**: Malformed progress events MUST be rejected by runtime consumers that use generated validation.

### I. CLI JSON Output Contracts

- **FR-068**: CLI commands that provide machine-readable JSON output MUST have explicit JSON output contracts before being treated as stable integration surfaces.
- **FR-069**: P0 MUST generate the progress-event JSON contract; P1 MUST add contracts for the worker IPC envelopes and the legacy `ppi rpc` compatibility surface. No other CLI JSON output is in scope for spec 011.
- **FR-070**: CLI JSON output schemas MUST be documented when generated.
- **FR-071**: CLI JSON output TypeScript artifacts MUST be generated only for outputs consumed by frontend or VS Code extension code.
- **FR-072**: CLI JSON schema validation MUST not require every human-readable CLI command to define a schema.

### J. Webview Protocol Contract

- **FR-073**: Webview postMessage protocol messages MUST have a single explicit source contract before being treated as stable.
- **FR-074**: Webview protocol generation MUST produce frontend TypeScript message types.
- **FR-075**: Webview protocol generation MUST produce VS Code extension TypeScript message types.
- **FR-076**: Webview protocol generation MUST produce generated protocol documentation.
- **FR-077**: Webview runtime message handlers MUST validate incoming messages at the boundary.
- **FR-078**: Webview protocol generation MUST remain separate from REST API generation.


### K. Worker IPC and Legacy RPC Compatibility

- **FR-079**: The existing Python `msgspec.Struct` request, response, event, and envelope models under `src/ppi/worker_ipc/` MUST be the sole source of truth for worker IPC generation.
- **FR-080**: The worker IPC generator MUST fail validation if the Python models cannot export a complete deterministic schema; it MUST NOT switch to a second source contract.
- **FR-081**: Worker IPC generation MUST produce Python protocol metadata/constants, frontend TypeScript types, VS Code extension TypeScript types, and generated documentation.
- **FR-082**: Worker IPC generated artifacts MUST contain protocol metadata, IDs, envelope declarations, schemas, and validators only.
- **FR-083**: Worker IPC generated artifacts MUST NOT contain handlers, socket loops, lifecycle logic, query execution, analysis orchestration, or storage writes.
- **FR-084**: Legacy `ppi rpc` compatibility MUST remain in scope because it is an existing supported command, but it MUST be represented only by generated method constants, schemas required by existing consumers, and documentation.
- **FR-085**: `contracts/rpc-methods.yaml` MUST be the sole source of truth for the legacy JSON-RPC compatibility catalog.
- **FR-086**: Every worker command ID, worker event ID, and legacy RPC method ID MUST be unique within its namespace.
- **FR-087**: Protocol version metadata MUST be explicit and generated documentation MUST identify worker IPC as primary and legacy stdio JSON-RPC as compatibility-only.


### L. Generated Documentation and Fixtures

- **FR-088**: Generated documentation MUST be written under a generated documentation directory.
- **FR-089**: Generated documentation MUST include an index of generated artifacts.
- **FR-090**: The generated artifact index MUST list source contract, generated files, generator name, validation command, and owner area.
- **FR-091**: Generated fixtures MUST be deterministic.
- **FR-092**: Generated fixtures MUST be safe to commit.
- **FR-093**: Generated fixtures MUST be usable by backend, frontend, or VS Code tests when those tests target the same contract.
- **FR-094**: Generated docs MUST NOT replace hand-written architecture documentation.

### M. Python Boundary Typing

- **FR-095**: The project MUST define generic result aliases for staged pipeline operations.
- **FR-096**: The project MUST define typed aliases for synchronous and asynchronous pipeline stages.
- **FR-097**: The project MUST define reusable JSON boundary aliases for JSON scalar, value, object, and row collections.
- **FR-098**: The project MUST define domain map aliases for common metric, line count, distribution, and edge-kind mappings.
- **FR-099**: Broad `object` parameters at complexity/metric boundaries MUST be replaced with concrete types or structural protocols.
- **FR-100**: Progress encode/decode boundaries MUST accept and return the explicit progress event union, not an unconstrained base struct.
- **FR-101**: Query/storage boundaries MUST avoid returning unconstrained `Any` in result types for stable query outputs.
- **FR-102**: First-phase type checking MUST target high-risk P0 boundary zones before whole-project strictness is required.
- **FR-103**: `make mypy-p0` MUST be blocking for exactly the paths listed in the typing architecture contract; whole-project mypy MUST NOT be added as a spec 011 CI gate.
- **FR-104**: Strict type checking for the entire project MUST NOT be required in the first implementation phase.

### N. Import Boundary Enforcement

- **FR-105**: The project MUST define intended Python import boundaries for generated code, code generation devtools, runtime, storage, query, and server/API packages.
- **FR-106**: Generated code MUST NOT import handwritten business/query/runtime/storage/server logic.
- **FR-107**: Runtime production code MUST NOT import code generation devtools.
- **FR-108**: Storage code MUST NOT import server/API code.
- **FR-109**: Import boundary checks MUST be introduced only after package boundaries are physically separated enough to avoid preserving known-bad architecture.
- **FR-110**: Import Linter MUST run as a report-only, non-blocking CI step in P1.
- **FR-111**: Spec 011 MUST NOT make Import Linter blocking; a separate future specification is required to change this policy.

### O. CI Organization

- **FR-112**: CI MUST separate static API contract checks from runtime API conformance checks.
- **FR-113**: CI MUST include non-REST contract validation and generated freshness checks.
- **FR-114**: CI MUST include type checking visibility for P0 typed boundary zones.
- **FR-115**: Runtime API conformance CI MUST depend on static API contract freshness.
- **FR-116**: Non-REST generated contract freshness failures MUST be reported separately from REST/OpenAPI freshness failures.
- **FR-117**: CI failures MUST allow a developer to distinguish stale generated files, runtime contract mismatch, type errors, import boundary violations, and test failures.

---

## Edge Cases

- **EC-001**: A source contract is valid YAML but missing required fields; validation fails before generation.
- **EC-002**: Two error codes use the same identifier; validation fails and no files are written.
- **EC-003**: A generated file was manually edited; freshness check regenerates or compares and fails due to drift.
- **EC-004**: A generator would write outside approved generated directories; validation fails before writing.
- **EC-005**: The runtime API server does not become ready within the configured timeout; runtime conformance fails and prints the server log location.
- **EC-006**: The fixture repository is missing or unanalyzable; runtime conformance fails before schema-based checks.
- **EC-007**: OpenAPI contains a domain parameter without fixture-matching examples/enums and without deterministic seeding; runtime conformance setup fails before Schemathesis runs with a clear reason.
- **EC-008**: The committed OpenAPI contract is stale but runtime behavior happens to match current code; static freshness still fails.
- **EC-009**: The committed generated TypeScript API type artifact is stale; static freshness fails even if backend tests pass.
- **EC-010**: A progress event has a new tag but generated TypeScript was not refreshed; generated freshness check fails.
- **EC-011**: A CLI command emits human-readable output only; it does not need a JSON schema.
- **EC-012**: A CLI command claims stable `--json` output but lacks a schema; validation fails once that command is in stable scope.
- **EC-014**: Import linter would fail many current imports before package refactoring; the gate remains prepared or non-blocking until boundaries are stabilized.
- **EC-015**: Type checking finds many legacy errors outside P0 boundary zones; first-phase typing does not block those zones unless configured as blocking.
- **EC-016**: Generated docs are stale but generated code is fresh; generated freshness still fails because docs are committed generated artifacts.
- **EC-017**: A deprecated public error code has no replacement/removal note; validation fails.
- **EC-018**: A runtime conformance request generates a value invalid for the fixture dataset; first-stage checks use bounded safe endpoints and examples to avoid false failures.

---

## Success Criteria

- **SC-001**: A developer can run one validation command and validate all configured non-REST contract sources.
- **SC-002**: A developer can run one generation command and regenerate all configured non-REST generated artifacts.
- **SC-003**: A developer can run one freshness command and detect stale generated artifacts.
- **SC-004**: Static API freshness checks cover OpenAPI JSON, bundled OpenAPI, and generated frontend API types.
- **SC-005**: Runtime API conformance can start the API against a fixture repository and check it against the committed API contract.
- **SC-006**: Error codes are defined once and generated into Python, frontend TypeScript, VS Code TypeScript, and docs.
- **SC-007**: Progress events are represented as a typed union and generated into JSON Schema, TypeScript types, VS Code types, and docs.
- **SC-008**: Generated files include deterministic headers with source and generator information.
- **SC-009**: Generated files do not contain timestamps or absolute machine-specific paths.
- **SC-010**: CI can distinguish stale REST artifacts, runtime API mismatch, stale non-REST generated files, typing failures, import boundary failures, and test failures.
- **SC-011**: P0 typed boundaries avoid unconstrained `Any`, `object`, raw JSON dict/list aliases, or generic result types where stable shapes exist.
- **SC-013**: Generated artifact documentation index lists source contracts, generated files, generator names, validation commands, and owner areas.
- **SC-014**: Import boundary rules are documented, executed in report-only mode, and produce a stored CI log without changing generated file contents or failing the job.
- **SC-015**: No feature in this specification introduces a second REST client generation path.
- **SC-016**: No generator introduced by this feature generates analysis business logic.

---

## Assumptions

- **A-001**: Spec 010 provides or will provide the REST/OpenAPI contract foundation and generated REST transport artifacts.
- **A-002**: The project uses Python 3.11 or newer.
- **A-003**: The project uses `uv` as the primary Python development dependency entrypoint.
- **A-004**: `uv sync --extra dev` is the required installation command for spec 011 dependencies; existing dependency groups may remain, but spec 011 commands MUST NOT depend on them.
- **A-005**: Runtime API conformance can use a stable local fixture repository.
- **A-006**: The first runtime conformance scope focuses on read-only endpoints.
- **A-007**: Some typing checks may start as non-blocking or P0-only.
- **A-008**: Import boundary checks may start non-blocking until package boundaries are refactored.
- **A-009**: Generated files are committed to the repository when they are part of cross-language or docs/test contracts.
- **A-010**: Handwritten query and analysis logic remains the source of business behavior.
- **A-011**: Generated docs are reference catalogs and do not replace architecture narrative documentation.

---

## Key Entities

- **Contract Source**: A human-owned schema, manifest, migration, or runtime model used as the source for validation and generation.
- **Generated Artifact**: A committed file derived from a contract source and not manually edited.
- **Generator**: Deterministic command that validates one or more sources and writes generated artifacts.
- **Generated Artifact Header**: Required header in generated files that identifies generated status, source, and generator.
- **Contract Validation Result**: Result of checking contract sources without writing generated files.
- **Generated Freshness Result**: Result of comparing generated output with committed files.
- **Runtime API Conformance Check**: Test that runs the API and checks responses against the committed API contract.
- **Fixture Repository**: Stable repository used to prepare data for runtime API conformance checks.
- **Error Code Entry**: Contracted error definition with code, category, status mapping, retryability, stability, and description.
- **Progress Event**: Tagged runtime event emitted by machine-readable CLI progress streams.
- **CLI JSON Contract**: JSON schema describing a stable machine-readable CLI output.
- **Webview Message Contract**: Schema describing messages exchanged between webview and extension processes.
- **Typed Boundary Alias**: Shared Python type alias for results, pipeline stages, JSON values, metric maps, and event unions.
- **Import Boundary Rule**: Architecture rule controlling allowed imports between generated, devtools, runtime, storage, query, and server layers.

---

## Out of Scope for This Specification

- DuckDB/storage schema generation.
- Migration catalog generation.
- Ibis descriptor generation.
- Full public REST API redesign.
- REST SDK generator selection.
- External SDK package publishing.
- Full plugin runtime implementation.
- Full strict typing across the entire project in the first phase.
- Blocking import-linter gate before package boundaries are stable.
- Full Schemathesis fuzzing of every endpoint in the first phase.
- Code generation for analysis algorithms or React components.

---

## Documentation Notes

- Implementation-specific tool choices belong in `plan.md`, but the spec intentionally fixes behavioral requirements and command names to remove ambiguity for implementation.
- The implementation plan must map these requirements to concrete files and commands in the current repository.
- The implementation plan must keep spec 010 REST SDK generation as the only REST SDK path.
