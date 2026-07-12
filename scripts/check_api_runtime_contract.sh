#!/usr/bin/env bash
set -euo pipefail

SCHEMA="${SCHEMA:-openapi/openapi.json}"
FIXTURE_REPO="${PPI_CONTRACT_FIXTURE_REPO:-tests/fixtures/api_contract_repo}"
PORT="${PPI_CONTRACT_PORT:-8765}"
LOG_FILE="${PPI_CONTRACT_LOG_FILE:-/tmp/ppi-api-contract.log}"
MAX_EXAMPLES="${SCHEMATHESIS_MAX_EXAMPLES:-25}"
BASE_URL="http://127.0.0.1:${PORT}"

echo "=== Runtime API Conformance ==="
echo "  Schema:      ${SCHEMA}"
echo "  Fixture:     ${FIXTURE_REPO}"
echo "  Port:        ${PORT}"
echo "  Max examples: ${MAX_EXAMPLES}"

# 1. Fail if schema is missing
if [ ! -f "${SCHEMA}" ]; then
    echo "FAIL: OpenAPI schema not found: ${SCHEMA}"
    exit 1
fi

# 2. Fail if fixture repo is missing
if [ ! -d "${FIXTURE_REPO}" ]; then
    echo "FAIL: Fixture repository not found: ${FIXTURE_REPO}"
    exit 1
fi

# 3. Analyze fixture repo
echo "--- Analyzing fixture repository ---"
uv run ppi --repo "${FIXTURE_REPO}" analyze --all-modules 2>&1 | tail -5

# 4. Start server
echo "--- Starting API server ---"
cleanup() {
    echo "--- Cleaning up server ---"
    if [ -n "${SERVER_PID:-}" ]; then
        kill "${SERVER_PID}" 2>/dev/null || true
        wait "${SERVER_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

uv run ppi --repo "${FIXTURE_REPO}" serve --port "${PORT}" > "${LOG_FILE}" 2>&1 &
SERVER_PID=$!

# 5. Wait for readiness via /api/v1/status
echo "--- Waiting for /api/v1/status readiness ---"
MAX_RETRIES=30
RETRY_INTERVAL=2
READY=false
for ((i=1; i<=MAX_RETRIES; i++)); do
    if curl -sf "${BASE_URL}/api/v1/status" > /dev/null 2>&1; then
        READY=true
        echo "Server ready after ${i}s"
        break
    fi
    sleep "${RETRY_INTERVAL}"
done

if [ "${READY}" != "true" ]; then
    echo "FAIL: Server did not become ready at ${BASE_URL}/api/v1/status"
    echo "--- Server log tail ---"
    tail -20 "${LOG_FILE}"
    exit 1
fi

# 7. Verify endpoint parameter coverage (basic check)
echo "--- Checking endpoint parameter coverage ---"
API_PATHS=$(uv run python -c "
import json
with open('${SCHEMA}') as f:
    spec = json.load(f)
paths = [p for p in spec.get('paths', {}) if p.startswith('/api/v1/')]
print('\n'.join(paths))
" 2>/dev/null || echo "")

if [ -z "${API_PATHS}" ]; then
    echo "WARN: No /api/v1/ endpoints found in schema"
fi

# 8. Run Schemathesis
echo "--- Running Schemathesis ---"
uv run st run \
    -u "${BASE_URL}" \
    --max-examples "${MAX_EXAMPLES}" \
    -m positive \
    --checks all \
    --suppress-health-check too_slow \
    --seed 42 \
    --include-path-regex "^/api/v1/" \
    "${SCHEMA}"

echo "=== Runtime API conformance passed. ==="
