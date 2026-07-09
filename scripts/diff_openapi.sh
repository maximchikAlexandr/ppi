#!/usr/bin/env bash
# scripts/diff_openapi.sh
# Non-blocking API diff. Before the first stable baseline the script always
# succeeds; the changelog is still printed for human review.
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

if [[ ! -f "$BASELINE" ]]; then
  echo "no baseline at $BASELINE; skipping diff (report-only mode before first stable baseline)"
  exit 0
fi

if ! command -v oasdiff >/dev/null 2>&1; then
  echo "oasdiff not found on PATH; install with: go install github.com/oasdiff/oasdiff/cmd/oasdiff@latest"
  exit 0
fi

echo "oasdiff changelog (non-blocking before baseline)"
oasdiff changelog "$BASELINE" "$CURRENT" || true
exit 0

# ponytail: post-baseline blocking path is unimplemented. When
# openapi/baseline/current.json is promoted (per
# docs/frontend-api-platform-migration.md baseline checklist), replace
# the `exit 0` above with:
#   oasdiff breaking "$BASELINE" "$CURRENT" || { echo "breaking API change vs baseline"; exit 1; }
# Until then this script is report-only and never blocks CI.
