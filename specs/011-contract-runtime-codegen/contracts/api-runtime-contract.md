# Contract: Runtime API Conformance

## Command

```bash
make api-runtime-contract
```

Delegates to:

```bash
bash scripts/check_api_runtime_contract.sh
```

## Required defaults

```text
SCHEMA=openapi/openapi.json
PPI_CONTRACT_PORT=8765
PPI_CONTRACT_FIXTURE_REPO=tests/fixtures/api_contract_repo
PPI_CONTRACT_LOG_FILE=/tmp/ppi-api-contract.log
SCHEMATHESIS_MAX_EXAMPLES=25
```

## Script behavior

The script MUST execute these steps in order:

1. fail if `openapi/openapi.json` is missing;
2. fail if `tests/fixtures/api_contract_repo` is missing;
3. run `uv run ppi --repo "$FIXTURE_REPO" analyze --all-modules`;
4. start `uv run ppi --repo "$FIXTURE_REPO" serve --port "$PORT"`;
5. wait for `/api/v1/status` readiness;
6. probe `/api/v1/status` only; any readiness failure aborts setup and legacy `/api/status` is never probed;
7. verify that all implemented `/api/v1/*` endpoints with domain parameters have fixture-compatible examples/enums or deterministic seeding;
8. run Schemathesis against committed `openapi/openapi.json` and `BASE_URL`;
9. kill the server on exit.

## Scope

Included:

```text
all implemented /api/v1/* endpoints
```

Excluded:

```text
legacy /api/* endpoints in Schemathesis
```

## Failure requirements

The command MUST fail when:

- schema file is missing;
- fixture repo is missing;
- fixture analysis fails;
- server does not become ready;
- required parameter seeding/examples are missing;
- runtime response violates committed OpenAPI.
