# OpenAPI Artifacts (parent dir)

The artifacts in `../` (the parent of this directory) are the source
of truth for the project:

- `../openapi.json` — current exported OpenAPI 3.1 schema (sorted keys, deterministic). Tracked in git.
- `../openapi.bundle.yaml` — bundled single-file OpenAPI artifact produced by Redocly. Tracked in git.
- `current.json` — frozen baseline copy used for blocking breaking-change detection. Tracked in git.

The contract is generated from the FastAPI app and validated by Spectral, Redocly,
and `oasdiff` (blocking once a baseline exists).

## Baseline promotion

The first stable baseline is committed at `current.json` (spec-010 P2). To deliberately ship
a breaking change, run `make api-bump-baseline` and add a note in `frontend/MIGRATION.md`.
