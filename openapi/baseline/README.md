# OpenAPI Artifacts

This directory stores the exported OpenAPI contract for the project:

- `openapi.json` — current exported OpenAPI 3.1 schema (sorted keys, deterministic).
- `openapi.bundle.yaml` — bundled single-file OpenAPI artifact produced by Redocly.
- `baseline/current.json` — frozen baseline copy used for blocking breaking-change detection.
- `baseline/README.md` — baseline promotion instructions and changelog rules.

The contract is generated from the FastAPI app and validated by Spectral, Redocly,
and `oasdiff` (non-blocking before the first stable baseline).

## Baseline promotion

The first stable baseline is declared only after the migration gate
described in `docs/frontend-api-platform-migration.md` is satisfied
(Graph, Tables, Metrics Dashboard all migrated to generated transport
plus adapters).

To promote the baseline:

```bash
# 1. Run all governance checks.
bash scripts/check_openapi.sh

# 2. Confirm `oasdiff` shows only intended changes.
bash scripts/diff_openapi.sh

# 3. Copy the current contract into the baseline slot.
cp openapi/openapi.json openapi/baseline/current.json

# 4. Commit `openapi/baseline/current.json` together with the migration gate.
git add openapi/baseline/current.json
git commit -m "promote /api/v1 baseline"
```

After promotion, `oasdiff breaking openapi/baseline/current.json openapi/openapi.json`
must return non-zero on breaking changes (the post-baseline check).

## Current baseline instructions

Until the first stable baseline is promoted, the `baseline/` directory
is intentionally empty and `scripts/diff_openapi.sh` runs in non-blocking
report-only mode.
