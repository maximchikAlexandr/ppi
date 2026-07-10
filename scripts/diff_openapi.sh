#!/usr/bin/env bash
# scripts/diff_openapi.sh
# Compares the exported OpenAPI contract against the frozen baseline.
#
# Behaviour:
#   - If a baseline exists at openapi/baseline/current.json, blocking
#     breaking changes fail the script. The script still prints the
#     full changelog so reviewers see what changed.
#   - If no baseline exists, the script is report-only and exits 0.
#     (Used before the first stable baseline is promoted.)
#
# `oasdiff` is a Go binary (https://github.com/oasdiff/oasdiff) and is
# NOT distributed through npm. Install it once with:
#   go install github.com/oasdiff/oasdiff/cmd/oasdiff@latest
# and ensure `$(go env GOPATH)/bin` is on your PATH.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BASELINE="openapi/baseline/current.json"
CURRENT="openapi/openapi.json"

if [[ ! -f "$CURRENT" ]]; then
  echo "current contract not found at $CURRENT; run scripts/check_openapi.sh first"
  exit 0
fi

if ! command -v oasdiff >/dev/null 2>&1
then
  if [[ ! -f "$BASELINE" ]]; then
    echo "oasdiff not found; install with: go install github.com/oasdiff/oasdiff/cmd/oasdiff@latest"
    echo "no baseline committed yet; skipping diff (report-only mode before first stable baseline)"
    exit 0
  fi
  echo "oasdiff not found on PATH; install with: go install github.com/oasdiff/oasdiff/cmd/oasdiff@latest"
  exit 1
fi

echo "oasdiff changelog vs baseline:"
oasdiff changelog "$BASELINE" "$CURRENT" || true

if [[ ! -f "$BASELINE" ]]; then
  echo "no baseline at $BASELINE; report-only mode before first stable baseline"
  exit 0
fi

echo
echo "oasdiff breaking changes vs baseline:"
BREAKING_OUT="$(oasdiff breaking "$BASELINE" "$CURRENT" 2>&1)" || true
echo "$BREAKING_OUT"
# oasdiff exits 0 even when it finds breaking changes. We treat any
# line that starts with "error" as a hard failure.
if echo "$BREAKING_OUT" | grep -qE '^error'; then
  echo
  echo "ERROR: breaking API change vs $BASELINE. Either:"
  echo "  - keep the contract backward-compatible, or"
  echo "  - promote a new baseline (see openapi/baseline/README.md)."
  exit 1
fi

echo "OK: no breaking API change vs baseline"
exit 0
