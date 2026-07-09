#!/usr/bin/env bash
# scripts/check_openapi.sh
# Order: export -> Spectral lint -> Redocly lint -> Redocly bundle.
# Exits non-zero on any failure. TS type generation is owned by
# `make api-types` (api-contract target), not duplicated here.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p openapi

echo "[1/4] Exporting OpenAPI"
uv run python scripts/export_openapi.py --output openapi/openapi.json

echo "[2/4] Spectral lint"
(cd frontend && ./node_modules/.bin/spectral lint ../openapi/openapi.json --ruleset ../.spectral.yaml)

echo "[3/4] Redocly lint"
(cd frontend && ./node_modules/.bin/redocly lint --config ../redocly.yaml ../openapi/openapi.json)

echo "[4/4] Redocly bundle"
(cd frontend && ./node_modules/.bin/redocly bundle --config ../redocly.yaml ../openapi/openapi.json -o ../openapi/openapi.bundle.yaml)

echo "OK"
