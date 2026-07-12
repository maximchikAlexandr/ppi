# Contract: Non-REST Code Generation Commands

## Commands

```bash
uv run ppi dev validate-contracts
uv run ppi dev generate-contracts
uv run ppi dev check-generated
```

Root Makefile aliases:

```bash
make validate-contracts
make generate
make check-generated
make contract-check
```

## validate-contracts

MUST:

- validate `contracts/errors.yaml`;
- validate `contracts/webview-protocol.schema.json`;
- validate the importability and schema exportability of `src/ppi/runtime/progress.py::ProgressEvent`;
- reject duplicate IDs;
- reject invalid generated output paths;
- write no generated files.

## generate-contracts

MUST:

- validate contracts first;
- generate errors artifacts;
- generate progress artifacts;
- generate webview artifacts;
- generate docs index and reference docs;
- format deterministic output;
- write only approved paths.

## check-generated

MUST:

- validate contracts;
- compare regenerated output against committed generated files;
- fail on stale, missing, or manually edited generated artifacts;
- print `uv run ppi dev generate-contracts` as the remediation command.

## Anti-requirements (spec 011 codegen scope)

The following are explicitly out of scope per review C1-C4 / D4:

- **No Python-duplicate of already-typed Python enums** — e.g. worker-IPC (StrEnum
  in `ppi.worker_ipc.protocol`) does NOT get a parallel generated module; source
  IS the single source of truth.
- **No docs-only generators** — Markdown aggregation (e.g. CLI JSON schema table)
  does not justify the codegen pipeline; inline or handwrite such files.
- **No single-target constant generators** — a generator must serve ≥2 target
  languages (Python + TS + Ajv) to justify the infrastructure.
- **No P2/P1 deferred generators** — placeholder generators that emit static
  "deferred" strings are deleted; implement the full multi-target generator when
  the feature is scoped, or write the doc page by hand.
- **Every generator MUST include a semantic self-check** — a `_demo()` or
  `__main__` block and/or an assertion test that verifies the generated artifact
  correctly validates a real fixture. Byte-equality freshness alone is
  insufficient (see D1/D5).

## Worker IPC error codes — by-design divergence

`ppi.worker_ipc.protocol.WorkerErrorCode` contains 6 codes (UNKNOWN_COMMAND,
WORKER_BUSY, UNKNOWN_QUERY, QUERY_FAILED, STORAGE_UNAVAILABLE, INTERNAL_ERROR).
`contracts/errors.yaml` (via `ppi.generated.errors.ErrorCode`) is intentionally a
**subset**: only `INTERNAL_ERROR` overlaps. Worker IPC = internal protocol;
HTTP API = public contract. If unification is needed, add worker codes to
`errors.yaml` with `stability: internal` and let codegen generate a single enum.

## Approved output roots

```text
src/ppi/generated/
vscode-extension/src/generated/
docs/generated/
contracts/progress-events.schema.json
```
