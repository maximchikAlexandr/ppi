# Quickstart: Runtime Contract Code Generation and Boundary Typing

## Prerequisites

From repository root:

```bash
uv sync --extra dev
cd frontend && npm ci
cd ..
```

The repository contains `vscode-extension/`, so install extension dependencies when validating generated extension artifacts:

```bash
cd vscode-extension && npm ci
cd ..
```

## P0a workflow

Validate contract sources:

```bash
make validate-contracts
```

Expected result:

```text
contracts/errors.yaml: ok
contracts/webview-protocol.schema.json: ok
src/ppi/runtime/progress.py::ProgressEvent: ok
```

Generate artifacts:

```bash
make generate
```

Expected generated/updated files:

```text
src/ppi/generated/errors.py
src/ppi/generated/progress_events_schema.py
frontend/src/generated/errorCodes.ts
frontend/src/generated/progressEvents.ts
frontend/src/generated/progressEventValidators.ts
frontend/src/generated/webviewProtocol.ts
frontend/src/generated/webviewProtocolValidators.ts
docs/generated/index.md
docs/generated/errors.md
docs/generated/progress-events.md
docs/generated/webview-protocol.md
contracts/progress-events.schema.json
```

Additional P1+P2 generated files:

```text
src/ppi/generated/worker_ipc_protocol.py
src/ppi/generated/rpc_methods.py
frontend/src/generated/workerIpcProtocol.ts
frontend/src/generated/rpcMethods.ts
frontend/src/generated/pluginManifest.ts
vscode-extension/src/generated/workerIpcProtocol.ts
vscode-extension/src/generated/rpcMethods.ts
docs/generated/worker-ipc-protocol.md
docs/generated/rpc-methods.md
docs/generated/plugin-manifest.md
```

Check generated freshness:

```bash
make check-generated
```

Expected result:

```text
All generated contract artifacts are fresh.
```

Run boundary typing:

```bash
make mypy-p0
```

Expected result:

```text
P0 boundary mypy passed.
```

Note: mypy-p0 may report type-arg or missing-stub warnings for
non-codegen dependencies. P0 artifacts typed with strict checks
are: `src/ppi/generated`, `src/ppi/devtools/codegen`,
`src/ppi/runtime/progress.py`, `src/ppi/contracts`,
`src/ppi/devtools/cli.py`, `src/ppi/types`.

## Static API artifact freshness

Run:

```bash
make api-contract
```

Expected freshness scope:

```text
openapi/openapi.json
openapi/openapi.bundle.yaml
frontend/src/api/generated/schema.d.ts
```

## P0b runtime API conformance

Ensure fixture exists:

```bash
test -d tests/fixtures/api_contract_repo
```

Run:

```bash
make api-runtime-contract
```

Expected behavior:

```text
analyze fixture repo
start ppi serve
wait for /api/v1/status only; abort on failure
run Schemathesis against all implemented /api/v1/* endpoints
exclude legacy /api/* from Schemathesis
```

## Failure scenarios to verify

1. Edit `contracts/errors.yaml` without running generation. `make check-generated` must fail.
2. Manually edit `frontend/src/generated/errorCodes.ts`. `make check-generated` must fail.
3. Remove `tests/fixtures/api_contract_repo`. `make api-runtime-contract` must fail before starting Schemathesis.
4. Remove required OpenAPI example for a parameterized `/api/v1` endpoint. `make api-runtime-contract` must fail during setup.
5. Add an invalid webview schema. `make validate-contracts` must fail.

## P1 worker IPC protocol check

After P0a/P0b, P1 adds worker IPC protocol generation. The intended validation command remains the same top-level command:

```bash
make validate-contracts
make generate
make check-generated
```

Expected P1 worker IPC generated files:

```text
src/ppi/generated/worker_ipc_protocol.py
frontend/src/generated/workerIpcProtocol.ts
vscode-extension/src/generated/workerIpcProtocol.ts
docs/generated/worker-ipc-protocol.md
```

The generated files must describe command/event IDs and protocol metadata only. They must not contain worker handler logic.

## P1 RPC method generation

```bash
make generate
```

Expected additional generated files:

```text
src/ppi/generated/rpc_methods.py
frontend/src/generated/rpcMethods.ts
vscode-extension/src/generated/rpcMethods.ts
docs/generated/rpc-methods.md
```

## P2 Plugin manifest schema

The plugin manifest generator produces types, schemas, and docs only.
No plugin loading behavior is implemented. Generated files:

```text
frontend/src/generated/pluginManifest.ts
docs/generated/plugin-manifest.md
```

## Architecture visibility (P1 report-only)

```bash
make architecture-check
```

This runs Import Linter with initial contracts. It is non-blocking
for all of spec 011. Making it blocking requires a separate
future specification.
