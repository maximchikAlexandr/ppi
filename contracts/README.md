# Contract Sources

This directory contains contract source files for the ppi project's runtime
boundary code generation. Each contract source defines a deterministic
boundary that generates typed artifacts (Python enums, TypeScript types,
JSON Schema, Ajv validators, reference docs).

The subdirectories and files here are owned by spec 011
(contract-runtime-codegen). Spec 010 (frontend-api-platform) owns the REST
SDK generation; nothing in this directory duplicates or replaces OpenAPI.

## Layout

```text
contracts/
  README.md
  errors.yaml                              # P0a — error catalog
  webview-protocol.schema.json             # P0a — webview postMessage schema
  progress-events.schema.json              # P0a — generated from Python model
  rpc-methods.yaml                         # P1  — legacy JSON-RPC manifest
  plugin-manifest.schema.json              # P2  — plugin metadata schema (types/docs only)
  cli/
    README.md                              # P1  — CLI JSON schema directory
    *.schema.json                          # P1  — stable CLI --json schemas
  fixtures/
    .gitkeep                               # P1  — generated contract fixtures
```

## Ownership

- P0a: errors, webview protocol, progress events (from Python model)
- P1: RPC methods, CLI JSON schemas, generated fixtures
- P2: Plugin manifest (types/docs only, no loading)

## Change Control

Contract sources are human-owned and reviewed. Generated artifacts under
`src/ppi/generated/`, `frontend/src/generated/`, `vscode-extension/src/generated/`,
`docs/generated/`, and `contracts/progress-events.schema.json` are machine-generated
from these sources. Manual edits to generated files are detected by
`make check-generated` and will fail CI.

## CI

```bash
make validate-contracts   # validate all contract sources
make generate             # regenerate all artifacts
make check-generated      # verify committed artifacts are fresh
```
