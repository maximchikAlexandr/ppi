#!/usr/bin/env bash
set -euo pipefail

FIVE_PATHS=(
    "src/ppi/generated"
    "src/ppi/devtools/codegen"
    "src/ppi/runtime/progress.py"
    "src/ppi/contracts"
    "src/ppi/devtools/cli.py"
)

EXISTING=()
for p in "${FIVE_PATHS[@]}"; do
    if [ -e "$p" ]; then
        EXISTING+=("$p")
    else
        echo "skip: $p not found"
    fi
done

if [ ${#EXISTING[@]} -eq 0 ]; then
    echo "Nothing to check."
    exit 0
fi

exec uv run mypy "${EXISTING[@]}"
