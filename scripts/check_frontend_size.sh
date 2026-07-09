#!/usr/bin/env bash
# scripts/check_frontend_size.sh
# Code-size budget: fail if any production JS chunk exceeds the
# configured byte limit. The limit is a soft one — bump it on
# legitimate growth, but every bump must be paired with a MIGRATION.md
# note explaining why.
#
# Vite's build output format is `<path>   <size> kB │ gzip: <gzipped> kB`.
# We anchor on lines that start with `dist/` and end with `kB` to ignore
# the gzip column.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/frontend"

LIMIT="${SIZE_BUDGET_KB:-900}"

BUILD_OUT="$(npm run build 2>&1)"
echo "$BUILD_OUT" | tail -20
echo

BAD=0
FOUND=0
while IFS= read -r line; do
  # Vite output: `dist/assets/index-XYZ.js   790.06 kB │ gzip:   228.26 kB`
  # We want the first kB value, not the gzipped one.
  if echo "$line" | grep -qE '^dist/.*\.js[[:space:]]+[0-9.]+ kB'; then
    FOUND=1
    SIZE_KB="$(echo "$line" | sed -E 's/^dist\/.*\.js[[:space:]]+([0-9.]+) kB.*/\1/')"
    SIZE_INT="$(printf "%.0f" "$SIZE_KB")"
    FILE="$(echo "$line" | awk '{print $1}')"
    if [ "$SIZE_INT" -gt "$LIMIT" ]; then
      echo "ERROR: $FILE is ${SIZE_KB}kB, exceeds size budget ${LIMIT}kB"
      BAD=1
    else
      echo "OK:   $FILE is ${SIZE_KB}kB"
    fi
  fi
done <<< "$BUILD_OUT"

if [ "$BAD" -ne 0 ]; then
  echo
  echo "Split the chunk, lazy-load the heavy route, or raise the budget in Makefile."
  exit 1
fi

if [ "$FOUND" -eq 0 ]; then
  echo "ERROR: no JS chunks found in build output. Did the build fail?"
  echo "Re-run 'cd frontend && npm run build' to see the actual error."
  exit 1
fi

echo "OK: all JS chunks under ${LIMIT}kB"
exit 0
