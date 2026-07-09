.PHONY: sync frontend tool update api-contract api-types api-lint api-diff api-boundaries api-freshness

sync:
	uv sync

frontend:
	cd frontend && npm install && npm run build

tool:
	uv tool install --editable --reinstall .

# ── API contract workflow ────────────────────────────────────────
# Single entrypoint: export OpenAPI, lint, bundle, generate TS types,
# run non-blocking diff, the frontend boundary scanner, and assert the
# regenerated artifacts match what is committed (freshness guard).
api-contract: api-lint api-types api-diff api-boundaries api-freshness

# Export OpenAPI + run Spectral + Redocly lint + Redocly bundle.
api-lint:
	bash scripts/check_openapi.sh

# Regenerate frontend TypeScript transport types from the exported
# contract. Output: frontend/src/api/generated/schema.d.ts.
api-types:
	cd frontend && npm run openapi:types

# Non-blocking API diff against the frozen baseline. Succeeds when no
# baseline exists; prints the changelog otherwise.
api-diff:
	bash scripts/diff_openapi.sh

# Forbidden-identifier and import-boundary scan for the generic frontend.
api-boundaries:
	cd frontend && npm run check:frontend-boundaries

# Freshness guard: regenerated OpenAPI + TS types must match the
# committed copies. Catches "changed Pydantic, forgot to commit
# regenerated contract" drift. Run after api-lint + api-types.
api-freshness:
	@git diff --exit-code -- openapi/openapi.json frontend/src/api/generated/schema.d.ts || { \
		echo ""; \
		echo "ERROR: regenerated contract artifacts differ from committed copies."; \
		echo "Run 'make api-contract' and commit openapi/openapi.json + frontend/src/api/generated/schema.d.ts."; \
		exit 1; \
	}

update: sync frontend tool
