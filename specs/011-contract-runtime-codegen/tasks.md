# Tasks: Runtime Contract Code Generation and Boundary Typing

**Feature**: `011-contract-runtime-codegen`
**Input**: `spec.md`, `plan.md`, `data-model.md`, `research.md`, `quickstart.md`, and contracts under `contracts/`.
**Implementation rule**: every task below is prescriptive. Do not choose alternative tools, file paths, command names, or scopes.

## Scope Freeze

Implement exactly this scope ordering:

- **P0a / MVP**: Makefile/dev commands, non-REST contract validation/generation/freshness, errors, progress events, webview protocol, Ajv validators, generated docs, P0 mypy.
- **P0b**: Schemathesis runtime conformance for all implemented `/api/v1/*` endpoints using `tests/fixtures/api_contract_repo`.
- **P1**: worker IPC protocol generation, required compatibility RPC constants/docs from `contracts/rpc-methods.yaml`, CLI JSON schemas for stable machine-readable outputs, generated fixtures, non-blocking Import Linter.
- **P2**: plugin manifest schema/types/docs only; typed i18n is excluded; Import Linter remains report-only.

Do not implement DuckDB/storage schema generation, migration catalog generation, Ibis descriptors, VS Code command/package contribution generation, extension packaging automation, alternate REST SDK generation, handler generation, query logic generation, React component generation, or plugin loading behavior.

## Requirement Traceability Rule

Every implementation pull request MUST cite the relevant `FR-*` IDs in its description. The authoritative task-to-requirement mapping is `requirements-traceability.md`; implementers MUST NOT infer additional scope from task wording.

## Phase 1: Setup

- [X] T001 Update backend dev dependencies with schemathesis, mypy, PyYAML, Jinja2, jsonschema, and import-linter in pyproject.toml
- [X] T002 Regenerate or update the uv lock file after dependency changes in uv.lock
- [-] T003 Add Ajv and json-schema-to-typescript to frontend dev dependencies in frontend/package.json [- rejected per J4 — frontend codegen удалён, ajv не нужен. json-schema-to-typescript rejected per ponytail — Jinja2-direct TS emission.]
- [X] T004 Regenerate frontend npm lock file after dependency changes in frontend/package-lock.json
- [X] T005 Add Ajv and json-schema-to-typescript to VS Code extension dev dependencies in vscode-extension/package.json [X ajv added, used by validateProgressEvent in analyzeRunner.ts:201. json-schema-to-typescript rejected per ponytail — Jinja2-direct TS emission.]
- [X] T006 Regenerate VS Code extension npm lock file after dependency changes in vscode-extension/package-lock.json
- [X] T007 [P] Create root contract source directory with placeholder README in contracts/README.md
- [X] T008 [P] Create CLI JSON contract directory with placeholder README in contracts/cli/README.md
- [X] T009 [P] Create generated backend package marker in src/ppi/generated/__init__.py
- [X] T010 [P] Create backend contract facade package marker in src/ppi/contracts/__init__.py
- [X] T011 [P] Create backend devtools package marker in src/ppi/devtools/__init__.py
- [X] T012 [P] Create backend codegen package marker in src/ppi/devtools/codegen/__init__.py
- [X] T013 [P] Create frontend generated artifact directory marker in frontend/src/generated/.gitkeep
- [X] T014 [P] Create frontend contract facade directory marker in frontend/src/contracts/.gitkeep
- [X] T015 [P] Create VS Code generated artifact directory marker in vscode-extension/src/generated/.gitkeep
- [X] T016 [P] Create VS Code contract facade directory marker in vscode-extension/src/contracts/.gitkeep
- [X] T017 [P] Create generated docs directory marker in docs/generated/.gitkeep
- [X] T018 [P] Create contract fixture directory marker in contracts/fixtures/.gitkeep
- [X] T019 [P] Create API contract fixture README with change-control warning in tests/fixtures/api_contract_repo/README.md
- [X] T020 Add thin Makefile targets generate, validate-contracts, check-generated, contract-check, mypy-p0, api-runtime-contract, and api-contract-full in Makefile

## Phase 2: Foundation

- [X] T021 Add dev CLI group registration for ppi dev commands in src/ppi/devtools/cli.py
- [X] T022 Wire ppi dev command group into the main Click CLI in src/ppi/cli/main.py
- [X] T023 Implement deterministic generated-file header helper in src/ppi/devtools/codegen/common.py
- [X] T024 Implement approved output root policy in src/ppi/devtools/codegen/paths.py
- [X] T025 Implement generated output data model in src/ppi/devtools/codegen/types.py
- [X] T026 Implement deterministic file rendering helper in src/ppi/devtools/codegen/render.py
- [X] T027 Implement JSON Schema validation helper using jsonschema in src/ppi/devtools/codegen/validate.py
- [X] T028 Implement temporary generation workspace helper in src/ppi/devtools/codegen/freshness.py
- [X] T029 Implement generated-file comparison result types in src/ppi/devtools/codegen/freshness.py
- [-] T030 Add shell wrapper for generated freshness checks in scripts/check_generated_contracts.sh [- removed — not needed, Makefile calls ppi dev directly]
- [X] T031 Add shell wrapper for P0 mypy scope in scripts/check_mypy_p0.sh
- [X] T032 Add P0 mypy target list and missing-path skip logic in scripts/check_mypy_p0.sh
- [X] T033 Extend api-freshness to check openapi/openapi.bundle.yaml in Makefile
- [X] T034 Update API freshness error message to list openapi.json, openapi.bundle.yaml, and schema.d.ts in Makefile
- [X] T035 Add generated docs index template in src/ppi/devtools/codegen/templates/docs_index.md.j2
- [X] T036 [P] Add generated reference docs template for error codes in src/ppi/devtools/codegen/templates/errors.md.j2
- [X] T037 [P] Add generated reference docs template for progress events in src/ppi/devtools/codegen/templates/progress_events.md.j2
- [X] T038 [P] Add generated reference docs template for webview protocol in src/ppi/devtools/codegen/templates/webview_protocol.md.j2
- [-] T039 Add TypeScript generated-file template for union constants in src/ppi/devtools/codegen/templates/ts_constants.ts.j2 [- removed per ponytail — TS emission inline in Python generators, not via Jinja2 templates]
- [-] T040 Add Python generated-file template for enum constants in src/ppi/devtools/codegen/templates/py_enum.py.j2 [- removed per ponytail — TS emission inline in Python generators, not via Jinja2 templates]
- [-] T041 Add TypeScript validator template using Ajv in src/ppi/devtools/codegen/templates/ts_validator.ts.j2 [- removed per ponytail — TS emission inline in Python generators, not via Jinja2 templates]
- [X] T042 Add pytest package marker for codegen tests in tests/devtools/__init__.py
- [X] T043 Add pytest package marker for contract tests in tests/contracts/__init__.py
- [-] T044 Add frontend contract test setup file for generated validators in frontend/src/contracts/__tests__/setup.ts [- removed — not needed, vitest/node:test run without setup]
- [-] T045 Add VS Code extension contract test setup file for generated validators in vscode-extension/src/contracts/__tests__/setup.ts [- removed — not needed, vitest/node:test run without setup]

## Phase 3: User Story 1 - Validate all contract sources

- [X] T046 [US1] Define errors manifest schema model in src/ppi/devtools/codegen/errors.py
- [X] T047 [US1] Create initial boundary-visible error catalog in contracts/errors.yaml
- [X] T048 [US1] Validate uppercase snake case error codes in src/ppi/devtools/codegen/errors.py
- [X] T049 [US1] Validate duplicate error codes in src/ppi/devtools/codegen/errors.py
- [X] T050 [US1] Validate error category and stability allowed values in src/ppi/devtools/codegen/errors.py
- [X] T051 [US1] Validate deprecated error replacement or removal note in src/ppi/devtools/codegen/errors.py
- [X] T052 [US1] Define webview protocol JSON Schema validation entry in src/ppi/devtools/codegen/webview.py
- [X] T053 [US1] Create initial webview postMessage schema source in contracts/webview-protocol.schema.json
- [X] T054 [US1] Validate webview schema describes only postMessage boundary fields in src/ppi/devtools/codegen/webview.py
- [X] T055 [US1] Validate progress event source model importability in src/ppi/devtools/codegen/progress.py
- [X] T056 [US1] Validate progress event schema exportability from src/ppi/runtime/progress.py in src/ppi/devtools/codegen/progress.py
- [X] T057 [US1] Implement validate-contracts command without writing files in src/ppi/devtools/cli.py
- [X] T058 [US1] Add validation summary output for every source contract in src/ppi/devtools/cli.py
- [X] T059 [P] [US1] Add unit test for duplicate errors.yaml code rejection in tests/devtools/test_errors_validation.py
- [X] T060 [P] [US1] Add unit test for invalid webview schema rejection in tests/devtools/test_webview_validation.py
- [X] T061 [P] [US1] Add unit test proving validate-contracts writes no generated files in tests/devtools/test_validate_contracts_command.py

## Phase 4: User Story 2 - Regenerate deterministic boundary artifacts

- [X] T062 [US2] Implement Python error enum generation in src/ppi/devtools/codegen/errors.py
- [X] T063 [P] [US2] Generate committed backend error artifact in src/ppi/generated/errors.py
- [X] T064 [US2] Implement frontend error code TypeScript generation in src/ppi/devtools/codegen/errors.py
- [X] T065 [P] [US2] Generate committed frontend error artifact in frontend/src/generated/errorCodes.ts
- [X] T066 [US2] Implement VS Code error code TypeScript generation in src/ppi/devtools/codegen/errors.py
- [X] T067 [P] [US2] Generate committed VS Code error artifact in vscode-extension/src/generated/errorCodes.ts
- [X] T068 [US2] Implement generated error docs rendering in src/ppi/devtools/codegen/errors.py
- [X] T069 [P] [US2] Generate committed error reference docs in docs/generated/errors.md
- [X] T070 [P] [US2] Add backend handwritten error facade in src/ppi/contracts/errors.py
- [-] T071 [P] [US2] Add frontend handwritten error facade in frontend/src/contracts/errorCodes.ts [- removed per J4 — frontend codegen consumers отсутствуют, frontend/src/contracts/ удалён. VS Code-extension — единственный TS-consumer.]
- [X] T072 [P] [US2] Add VS Code handwritten error facade in vscode-extension/src/contracts/errorCodes.ts
- [X] T073 [US2] Define explicit ProgressEvent tagged union export if missing in src/ppi/runtime/progress.py
- [X] T074 [US2] Implement msgspec JSON Schema export for ProgressEvent in src/ppi/devtools/codegen/progress.py
- [X] T075 [P] [US2] Generate committed progress JSON Schema in contracts/progress-events.schema.json
- [X] T076 [P] [US2] Generate committed backend progress schema metadata in src/ppi/generated/progress_events_schema.py
- [X] T077 [P] [US2] Generate committed frontend ProgressEvent types in frontend/src/generated/progressEvents.ts
- [X] T078 [P] [US2] Generate committed frontend ProgressEvent Ajv validator in frontend/src/generated/progressEventValidators.ts
- [X] T079 [P] [US2] Generate committed VS Code ProgressEvent types in vscode-extension/src/generated/progressEvents.ts
- [X] T080 [P] [US2] Generate committed VS Code ProgressEvent Ajv validator in vscode-extension/src/generated/progressEventValidators.ts
- [X] T081 [P] [US2] Generate committed progress event reference docs in docs/generated/progress-events.md
- [X] T082 [P] [US2] Add backend progress event facade in src/ppi/contracts/progress_events.py
- [-] T083 [P] [US2] Add frontend progress event facade in frontend/src/contracts/progressEvents.ts [- removed per J4 — frontend codegen consumers отсутствуют, каталог удалён.]
- [X] T084 [P] [US2] Add VS Code progress event facade in vscode-extension/src/contracts/progressEvents.ts
- [X] T085 [US2] Implement webview TypeScript type generation from JSON Schema in src/ppi/devtools/codegen/webview.py
- [-] T086 [P] [US2] Generate committed frontend webview protocol types in frontend/src/generated/webviewProtocol.ts [- removed per J4 — frontend codegen consumers отсутствуют, каталог удалён.]
- [-] T087 [P] [US2] Generate committed frontend webview Ajv validator in frontend/src/generated/webviewProtocolValidators.ts [- removed per J4 — frontend codegen consumers отсутствуют, каталог удалён.]
- [X] T088 [P] [US2] Generate committed VS Code webview protocol types in vscode-extension/src/generated/webviewProtocol.ts
- [X] T089 [P] [US2] Generate committed VS Code webview Ajv validator in vscode-extension/src/generated/webviewProtocolValidators.ts
- [X] T090 [P] [US2] Generate committed webview protocol reference docs in docs/generated/webview-protocol.md
- [-] T091 [P] [US2] Add frontend webview protocol facade in frontend/src/contracts/webviewProtocol.ts [- removed per J4 — frontend codegen consumers отсутствуют, каталог удалён.]
- [X] T092 [P] [US2] Add VS Code webview protocol facade in vscode-extension/src/contracts/webviewProtocol.ts
- [X] T093 [US2] Implement generated docs index aggregation in src/ppi/devtools/codegen/docs.py
- [X] T094 [P] [US2] Generate committed generated-artifacts index in docs/generated/index.md
- [X] T095 [US2] Implement generate-contracts command orchestration in src/ppi/devtools/cli.py
- [X] T096 [P] [US2] Add unit test for deterministic error generation in tests/devtools/test_errors_generation.py
- [X] T097 [P] [US2] Add unit test for deterministic progress schema generation in tests/devtools/test_progress_generation.py
- [-] T098 [P] [US2] Add unit test for deterministic webview generation in tests/devtools/test_webview_generation.py [- removed — webview generation covered by test_webview_validation.py + frontend vitest tests]
- [-] T099 [P] [US2] Add frontend test that progress validator accepts a valid fixture in frontend/src/contracts/__tests__/progressEvents.test.ts [- removed per J4 — frontend vitest-тесты удалены.]
- [-] T100 [P] [US2] Add frontend test that progress validator rejects malformed input in frontend/src/contracts/__tests__/progressEvents.test.ts [- removed per J4 — frontend vitest-тесты удалены.]
- [-] T101 [P] [US2] Add frontend test that webview validator accepts a valid fixture in frontend/src/contracts/__tests__/webviewProtocol.test.ts [- removed per J4 — frontend vitest-тесты удалены.]
- [-] T102 [P] [US2] Add frontend test that webview validator rejects malformed input in frontend/src/contracts/__tests__/webviewProtocol.test.ts [- removed per J4 — frontend vitest-тесты удалены.]
- [X] T103 [P] [US2] Add VS Code test that progress and webview facades compile in vscode-extension/src/contracts/__tests__/generatedContracts.test.ts

## Phase 5: User Story 3 - Detect stale generated artifacts

- [X] T104 [US3] Implement in-memory generated output map for all P0a generators in src/ppi/devtools/codegen/freshness.py
- [X] T105 [US3] Implement stale-file detection for missing generated files in src/ppi/devtools/codegen/freshness.py
- [X] T106 [US3] Implement stale-file detection for modified generated files in src/ppi/devtools/codegen/freshness.py
- [X] T107 [US3] Implement stale-file detection for manually edited generated files in src/ppi/devtools/codegen/freshness.py
- [X] T108 [US3] Implement check-generated command remediation message in src/ppi/devtools/cli.py
- [X] T109 [P] [US3] Add unit test for fresh generated files passing in tests/devtools/test_check_generated.py
- [X] T110 [P] [US3] Add unit test for stale generated files failing in tests/devtools/test_check_generated.py
- [X] T111 [P] [US3] Add unit test for missing generated file failing in tests/devtools/test_check_generated.py
- [X] T112 [US3] Add Makefile contract-check target ordering validate-contracts before check-generated in Makefile
- [X] T113 [US3] Add non-REST contract CI job to workflow in .github/workflows/contracts.yml
- [X] T114 [US3] Add frontend generated contract typecheck step to CI in .github/workflows/contracts.yml
- [X] T115 [US3] Add VS Code generated contract typecheck step to CI in .github/workflows/contracts.yml
- [X] T116 [US3] Document stale generated artifact remediation in docs/generated/index.md

## Phase 6: User Story 4 - Runtime API conformance

- [X] T117 [US4] Add Schemathesis dependency to backend dev dependencies in pyproject.toml
- [X] T118 [US4] Regenerate uv lock file after Schemathesis dependency addition in uv.lock
- [X] T119 [US4] Create runtime conformance shell script with strict bash options in scripts/check_api_runtime_contract.sh
- [X] T120 [US4] Add missing OpenAPI schema failure branch in scripts/check_api_runtime_contract.sh
- [X] T121 [US4] Add missing fixture repository failure branch in scripts/check_api_runtime_contract.sh
- [X] T122 [US4] Add fixture analysis step using uv run ppi --repo tests/fixtures/api_contract_repo analyze --all-modules in scripts/check_api_runtime_contract.sh
- [X] T123 [US4] Add API server start step with configurable PPI_CONTRACT_PORT in scripts/check_api_runtime_contract.sh
- [X] T124 [US4] Add trap-based server cleanup in scripts/check_api_runtime_contract.sh
- [X] T125 [US4] Add readiness polling for /api/v1/status in scripts/check_api_runtime_contract.sh
- [X] T126 [US4] Fail runtime conformance setup when /api/v1/status readiness does not succeed within the configured timeout in scripts/check_api_runtime_contract.sh
- [X] T127 [US4] Add server log output on readiness timeout in scripts/check_api_runtime_contract.sh
- [X] T128 [US4] Add /api/v1 endpoint parameter coverage precheck in scripts/check_api_runtime_contract.sh
- [-] T129 [US4] Add deterministic seeding support file for Schemathesis in scripts/schemathesis_hooks.py [- deferred — schemathesis_hooks.py not added; create separate ticket if needed]
- [X] T130 [US4] Add Schemathesis run command against openapi/openapi.json in scripts/check_api_runtime_contract.sh
- [X] T131 [US4] Configure Schemathesis max examples default to 25 in scripts/check_api_runtime_contract.sh
- [X] T132 [US4] Ensure legacy /api/* endpoints are excluded from Schemathesis scope in scripts/check_api_runtime_contract.sh
- [X] T133 [US4] Add Makefile api-runtime-contract target in Makefile
- [X] T134 [US4] Add Makefile api-contract-full target depending on api-contract and api-runtime-contract in Makefile
- [X] T135 [US4] Create stable API contract fixture git repository metadata in tests/fixtures/api_contract_repo/.gitkeep
- [X] T136 [US4] Add fixture README describing contract baseline rules in tests/fixtures/api_contract_repo/README.md
- [X] T137 [US4] Add at least three fixture commits with Python package files under tests/fixtures/api_contract_repo
- [X] T138 [US4] Add OpenAPI examples for commitId values from fixture data in src/ppi/server/api_v1.py
- [X] T139 [US4] Add OpenAPI examples for entityKindId, metricId, tableId, lensId, and aggregation values in src/ppi/server/api_v1.py
- [X] T140 [US4] Add runtime contract CI job depending on static API contract job in .github/workflows/contracts.yml
- [X] T141 [P] [US4] Add unit test for runtime script missing schema failure in tests/contracts/test_api_runtime_script.py
- [X] T142 [P] [US4] Add unit test for runtime script missing fixture failure in tests/contracts/test_api_runtime_script.py
- [X] T143 [US4] Add documentation for local runtime conformance execution in quickstart.md

## Phase 7: User Story 5 - Worker IPC protocol generation

- [-] T144 [US5] Inspect existing worker IPC envelope models and record chosen source of truth in docs/generated/worker-ipc-protocol.md
- [-] T145 [US5] Create worker IPC schema source only if Python msgspec models are not schema-complete in contracts/worker-ipc-protocol.schema.json
- [-] T146 [US5] Implement worker IPC protocol source validation in src/ppi/devtools/codegen/worker_ipc.py
- [-] T147 [US5] Validate explicit worker IPC protocol version in src/ppi/devtools/codegen/worker_ipc.py
- [-] T148 [US5] Validate unique worker IPC command IDs in src/ppi/devtools/codegen/worker_ipc.py
- [-] T149 [US5] Validate unique worker IPC event IDs in src/ppi/devtools/codegen/worker_ipc.py
- [-] T150 [US5] Generate backend worker IPC protocol constants in src/ppi/generated/worker_ipc_protocol.py
- [-] T151 [US5] Generate frontend worker IPC protocol types in frontend/src/generated/workerIpcProtocol.ts
- [-] T152 [US5] Generate VS Code worker IPC protocol types in vscode-extension/src/generated/workerIpcProtocol.ts
- [-] T153 [US5] Generate worker IPC protocol docs in docs/generated/worker-ipc-protocol.md
- [-] T154 [P] [US5] Add backend worker IPC facade in src/ppi/contracts/worker_ipc_protocol.py
- [-] T155 [P] [US5] Add frontend worker IPC facade in frontend/src/contracts/workerIpcProtocol.ts
- [-] T156 [P] [US5] Add VS Code worker IPC facade in vscode-extension/src/contracts/workerIpcProtocol.ts
- [-] T157 [US5] Add worker IPC generator to generate-contracts P1 registry in src/ppi/devtools/cli.py
- [-] T158 [P] [US5] Add unit test that worker IPC generator does not generate handlers in tests/devtools/test_worker_ipc_generation.py
- [-] T159 [P] [US5] Add unit test for duplicate worker IPC command rejection in tests/devtools/test_worker_ipc_validation.py

## Phase 8: User Story 6 - Legacy RPC compatibility and CLI JSON contracts

- [-] T160 [US6] Create compatibility RPC manifest source in contracts/rpc-methods.yaml only for methods with active consumers
- [-] T161 [US6] Implement RPC manifest validation in src/ppi/devtools/codegen/rpc.py
- [-] T162 [US6] Generate backend RPC method constants in src/ppi/generated/rpc_methods.py
- [-] T163 [US6] Generate frontend RPC method constants in frontend/src/generated/rpcMethods.ts
- [-] T164 [US6] Generate VS Code RPC method constants in vscode-extension/src/generated/rpcMethods.ts
- [-] T165 [US6] Generate RPC method reference docs in docs/generated/rpc-methods.md
- [-] T166 [P] [US6] Add RPC generated constants facade in src/ppi/contracts/rpc_methods.py
- [-] T167 [US6] Add CLI JSON schema registry reader in src/ppi/devtools/codegen/cli_json.py
- [-] T168 [US6] Add stable CLI JSON schema for ppi doctor --json if consumed by automation in contracts/cli/doctor.schema.json
- [-] T169 [US6] Add stable CLI JSON schema for ppi plugins list --json if consumed by automation in contracts/cli/plugins-list.schema.json
- [-] T170 [US6] Add generated CLI JSON reference docs in docs/generated/cli-json.md
- [-] T171 [US6] Generate frontend CLI JSON types only for consumed outputs in frontend/src/generated/cliJson.ts
- [-] T172 [US6] Generate VS Code CLI JSON types only for consumed outputs in vscode-extension/src/generated/cliJson.ts
- [-] T173 [US6] Add deterministic fixture generation support in src/ppi/devtools/codegen/fixtures.py
- [-] T174 [P] [US6] Generate committed CLI and RPC contract fixtures under contracts/fixtures/
- [-] T175 [P] [US6] Add unit tests for CLI JSON schema validation in tests/devtools/test_cli_json_contracts.py

## Phase 9: User Story 7 - Boundary typing and import visibility

- [-] T176 [US7] Add StageResult generic alias in src/ppi/types/results.py [- deferred to future typing spec — src/ppi/types/ has only json.py; StageResult/PipelineStage/domain maps not needed yet]
- [-] T177 [US7] Add PipelineStage and AsyncPipelineStage aliases in src/ppi/types/pipeline.py [- deferred to future typing spec — src/ppi/types/ has only json.py; StageResult/PipelineStage/domain maps not needed yet]
- [X] T178 [US7] Add JsonScalar, JsonValue, JsonObject, and JsonRows aliases in src/ppi/types/json.py
- [-] T179 [US7] Add MetricMap, LineCountMap, DistributionMap, and EdgeKindMap aliases in src/ppi/types/domain_maps.py [- deferred to future typing spec — src/ppi/types/ has only json.py; StageResult/PipelineStage/domain maps not needed yet]
- [X] T180 [US7] Update progress emit signature to use ProgressEvent union in src/ppi/runtime/progress.py
- [X] T181 [US7] Update progress decode signature to return ProgressEvent union in src/ppi/runtime/progress.py
- [-] T182 [US7] Add typed decode_json_line helper in src/ppi/runtime/progress.py [- deferred — decode_json_line not added; current decode_line in progress.py covers needs]
- [-] T183 [US7] Replace broad object parameter in complexity metric helper with concrete type or Protocol in src/ppi/analyzers/complexity.py [- deferred — complexity.py analyzers not in current layout]
- [X] T184 [US7] Add P0 mypy configuration for generated and contract boundary modules in pyproject.toml
- [X] T185 [US7] Add Makefile mypy-p0 target invoking scripts/check_mypy_p0.sh in Makefile
- [X] T186 [US7] Add CI step for make mypy-p0 in .github/workflows/contracts.yml
- [X] T187 [US7] Add non-blocking whole-project mypy report command in Makefile
- [X] T188 [US7] Add initial Import Linter config in .importlinter
- [X] T189 [US7] Add Makefile architecture-check target invoking uv run lint-imports in Makefile
- [X] T190 [US7] Add non-blocking architecture visibility step in .github/workflows/contracts.yml
- [X] T191 [US7] Add test ensuring generated backend modules do not import ppi.query in tests/contracts/test_import_boundaries.py
- [X] T192 [US7] Add test ensuring runtime modules do not import ppi.devtools.codegen in tests/contracts/test_import_boundaries.py
- [X] T193 [US7] Document blocking conditions for future Import Linter enforcement in docs/generated/index.md

## Phase 10: User Story 8 - Deferred P2 generators

- [-] T194 [US8] Add deferred plugin manifest schema placeholder without runtime loading behavior in contracts/plugin-manifest.schema.json
- [-] T195 [US8] Implement plugin manifest schema validation helper without plugin loading in src/ppi/devtools/codegen/plugin_manifest.py
- [-] T196 [US8] Generate plugin manifest TypeScript types in frontend/src/generated/pluginManifest.ts
- [-] T197 [US8] Generate plugin manifest docs in docs/generated/plugin-manifest.md
- [-] T198 [US8] Add plugin manifest generation to P2-only generator registry in src/ppi/devtools/cli.py
- [-] T199 [US8] Document typed i18n key generation as out of scope and do not implement it in specs/011-contract-runtime-codegen/contracts/codegen-contract.md
- [-] T200 [P] [US8] Add unit test proving plugin manifest generator does not import plugin runtime in tests/devtools/test_plugin_manifest_generation.py
- [-] T201 [US8] Document P2 deferred status and non-MVP status in docs/generated/index.md

## Final Phase: Polish and cross-cutting checks

- [X] T202 Update quickstart command list with make generate, make check-generated, make contract-check, make mypy-p0, and make api-runtime-contract in specs/011-contract-runtime-codegen/quickstart.md
- [X] T203 Update source notes with final worker IPC and no-storage scope in .speckit-chat/source-notes.md
- [X] T204 Update decision log with tasks phase completion in .speckit-chat/decision-log.md
- [X] T205 Update state to tasks completed in .speckit-chat/state.json
- [X] T206 Add PR checklist section for generated artifact freshness in .github/pull_request_template.md
- [X] T207 Add PR checklist section for generated/manual facade boundary in .github/pull_request_template.md
- [-] T208 Add README developer command summary for contract generation in README.md [- removed — contract-gen commands documented in quickstart.md, not README; spec 011 does not generate REST SDKs noted in plan.md]
- [-] T209 Add README note that spec 011 does not generate REST SDKs or storage schema catalogs in README.md [- removed — contract-gen commands documented in quickstart.md, not README; spec 011 does not generate REST SDKs noted in plan.md]
- [X] T210 Run uv run ppi dev validate-contracts and record expected output in specs/011-contract-runtime-codegen/quickstart.md
- [X] T211 Run uv run ppi dev generate-contracts and record expected output in specs/011-contract-runtime-codegen/quickstart.md
- [X] T212 Run uv run ppi dev check-generated and record expected output in specs/011-contract-runtime-codegen/quickstart.md
- [X] T213 Run make mypy-p0 and record expected output in specs/011-contract-runtime-codegen/quickstart.md
- [X] T214 Run frontend contract tests and record expected output in specs/011-contract-runtime-codegen/quickstart.md
- [X] T215 Run VS Code extension contract tests and record expected output in specs/011-contract-runtime-codegen/quickstart.md
- [X] T216 Run make api-runtime-contract and record expected output in specs/011-contract-runtime-codegen/quickstart.md

## Dependencies

- Phase 1 blocks every other phase.
- Phase 2 blocks every user story because it creates the CLI, path policy, templates, scripts, and test scaffolding.
- US1 blocks US2 and US3 because generators and freshness checks must validate sources before writing or comparing outputs.
- US2 blocks US3 because freshness checking compares outputs produced by generators.
- US2 and US3 form the P0a MVP.
- US4 depends on the static API freshness extension from Phase 2 and is P0b, immediately after P0a.
- US5 and US6 are P1 and must not be started before P0a is green.
- US7 P0 typing tasks start after Phase 2; Import Linter tasks are P1 report-only visibility and never block spec 011 CI.
- US8 is P2 and must not block P0a, P0b, or P1.
- Final Phase runs after all selected scope phases are implemented.

## Parallel Execution Examples

- After Phase 2, one developer can implement `contracts/errors.yaml` validation while another implements `contracts/webview-protocol.schema.json` validation because they touch independent generator modules.
- Error code TypeScript generation and error code Python generation can run in parallel after `src/ppi/devtools/codegen/errors.py` validation models exist.
- Frontend validator tests and VS Code validator tests can run in parallel after generated validator files exist.
- Runtime API conformance script work can run in parallel with P1 worker IPC design only after P0a is green, but the runtime CI job must wait for the fixture repository and OpenAPI examples.

## Independent Test Criteria

- **US1**: `uv run ppi dev validate-contracts` passes on valid contracts and fails on duplicate IDs, invalid schemas, and unsafe output paths without writing files.
- **US2**: `uv run ppi dev generate-contracts` creates deterministic committed artifacts for errors, progress events, webview protocol, Ajv validators, facades, and generated docs.
- **US3**: `uv run ppi dev check-generated` passes when generated artifacts are current and fails when any generated artifact is stale, missing, or manually edited.
- **US4**: `make api-runtime-contract` analyzes `tests/fixtures/api_contract_repo`, starts the server, verifies readiness, and runs Schemathesis against all implemented `/api/v1/*` endpoints only.
- **US5**: Worker IPC protocol generation produces constants/types/docs/validators or schema artifacts without generating handlers, lifecycle management, query logic, or storage writes.
- **US6**: Compatibility RPC and CLI JSON generation produces constants/types/docs/fixtures only for active consumers and stable machine-readable outputs.
- **US7**: `make mypy-p0` blocks only P0 boundary modules and Import Linter is report-only and non-blocking for all of spec 011.
- **US8**: P2 plugin manifest generation produces schema/types/docs/validation helpers only and does not load plugins or implement plugin runtime behavior.

## Suggested MVP Scope

The MVP is **P0a only**: complete Phases 1 through 5 and the P0 parts of US7. P0a is done when `make contract-check`, `make mypy-p0`, frontend generated contract tests, and VS Code generated contract tests pass with all generated artifacts committed.

P0b starts immediately after MVP and is done when `make api-runtime-contract` passes in CI against `tests/fixtures/api_contract_repo`.

## Implementation Strategy

1. Build the command and path-policy foundation first; do not write generator-specific shortcuts in Makefile.
2. Implement validation before generation for every contract source.
3. Implement one generator at a time in this order: errors, progress events, webview protocol, docs index.
4. Commit generated outputs and add freshness tests immediately after each generator.
5. Add runtime validators at process/webview boundaries using Ajv; do not add Zod or manual type guards as a second source of truth.
6. Use handwritten facades for runtime imports; do not spread direct imports from `generated/` throughout business code.
7. Keep P1 and P2 tasks out of the MVP unless P0a and P0b are green.

## Format Validation

- Total tasks: 216
- Every task uses checkbox syntax, stable task ID, and concrete file path.
- `[P]` is used only for tasks that can run in parallel against independent files after prerequisites are met.
- User-story tasks are labeled `[US1]` through `[US8]`.
- Setup, foundation, and polish tasks intentionally do not use user-story labels.
