.PHONY: sync frontend tool update api-contract api-types api-lint api-diff api-boundaries api-freshness api-bump-baseline boundaries-selftest size-budget i18n-freshness

sync:
	uv sync

frontend:
	cd frontend && npm install && npm run build

tool:
	uv tool install --editable --reinstall .

# ── API contract workflow ────────────────────────────────────────
# Single entrypoint: export OpenAPI, lint, bundle, generate TS types,
# run blocking diff (after baseline is promoted), the frontend
# boundary scanner, i18n freshness, code-size budget, and assert the
# regenerated artifacts match what is committed (freshness guard).
api-contract: api-lint api-types api-diff api-boundaries i18n-freshness size-budget api-freshness

# Export OpenAPI + run Spectral + Redocly lint + Redocly bundle.
api-lint:
	bash scripts/check_openapi.sh

# Regenerate frontend TypeScript transport types from the exported
# contract. Output: frontend/src/api/generated/schema.d.ts.
api-types:
	cd frontend && npm run openapi:types

# API diff against the frozen baseline. Succeeds when there are no
# breaking changes vs the baseline. Report-only if no baseline exists.
api-diff:
	bash scripts/diff_openapi.sh

# Forbidden-identifier and import-boundary scan for the generic frontend.
api-boundaries: boundaries-selftest
	cd frontend && npm run check:frontend-boundaries

# Smoke test: each rule in scripts/check_frontend_boundaries.py must
# fire on its positive case. Catches regressions in the regex set.
boundaries-selftest:
	uv run python scripts/check_frontend_boundaries.py --self-test

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

# Promote the current OpenAPI export to the frozen baseline. Use this
# only when you intend to ship a backwards-incompatible contract change.
# `make api-diff` will then block on the next breaking change.
api-bump-baseline:
	@test -f openapi/openapi.json || { echo "openapi/openapi.json not found; run 'make api-lint' first"; exit 1; }
	cp openapi/openapi.json openapi/baseline/current.json
	@echo "Promoted openapi/openapi.json -> openapi/baseline/current.json"
	@echo "Update frontend/MIGRATION.md with the breaking-change note before committing."

# Code-size budget: fail if any production JS chunk exceeds the configured
# byte limit (SIZE_BUDGET_KB, default 900). The limit is a soft one —
# bump it on legitimate growth, but every bump must be paired with a
# MIGRATION.md note explaining why.
size-budget:
	bash scripts/check_frontend_size.sh

# i18n freshness guard: locale files must be in lockstep with the
# keys extracted from source. Run 'npm run i18n:extract' (or
# 'make i18n-freshness-fix') to update them.
i18n-freshness:
	cd frontend && npm run i18n:check

update: sync frontend tool
