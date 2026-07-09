# Contract: API Governance and SDK Generation

**Feature**: `010-frontend-api-platform`  
**Status**: Hardened draft; implementation not yet complete

## 1. Required Files

```text
openapi/openapi.json
openapi/openapi.bundle.yaml
openapi/baseline/README.md
.spectral.yaml
redocly.yaml
scripts/export_openapi.py
scripts/check_openapi.sh
scripts/diff_openapi.sh
frontend/src/api/generated/schema.d.ts
frontend/src/api/generated/client.ts
```

## 2. Required NPM Dev Dependencies

Add to `frontend/package.json` dev dependencies or root package tooling if the project introduces root JS tooling:

```text
@redocly/cli
@stoplight/spectral-cli
openapi-typescript
openapi-fetch
oasdiff or documented oasdiff runner
```

If `oasdiff` is installed as a binary outside npm, document the exact invocation in `scripts/diff_openapi.sh`.

## 3. OpenAPI Export Command

`scripts/export_openapi.py` MUST export the FastAPI OpenAPI document without starting a long-running server.

Required invocation:

```bash
uv run python scripts/export_openapi.py --output openapi/openapi.json
```

Output rules:

- The file MUST contain OpenAPI 3.1-compatible content.
- Public `/api/v1` schemas MUST expose `camelCase` fields.
- `operationId` values MUST be stable.
- Legacy/internal endpoints MAY appear in the exported contract.

## 4. Spectral Rules

`.spectral.yaml` MUST enforce at least:

- every public `/api/v1` operation has `operationId`;
- every public `/api/v1` operation has `tags`;
- every public `/api/v1` operation has `summary`;
- every public `/api/v1` operation has a `2xx` response;
- every public `/api/v1` operation documents the common error response;
- no public/generic endpoint exists outside `/api/v1`;
- public `/api/v1` schemas use `camelCase` property names;
- public `/api/v1` request parameter names are consistent across endpoints (e.g., `entityKindId`, `commitId`, `targetId` are used identically wherever they appear).

## 5. Redocly Rules

`redocly.yaml` MUST allow:

```bash
npx redocly lint openapi/openapi.json
npx redocly bundle openapi/openapi.json -o openapi/openapi.bundle.yaml
```

`openapi/openapi.bundle.yaml` is a publishable artifact but is not the stable baseline by itself.

## 6. Frontend Generation Command

Required invocation:

```bash
npx openapi-typescript openapi/openapi.json -o frontend/src/api/generated/schema.d.ts
```

`openapi-fetch` MUST be used by `frontend/src/api/generated/client.ts` or `frontend/src/api/http.ts`.

Generated files may include full OpenAPI operations. Generic frontend code must not import generated files directly.

## 7. oasdiff Command

Before stable baseline:

```bash
scripts/diff_openapi.sh
```

Rules:

- It produces a diff or changelog report.
- It does not fail CI before stable baseline.

After stable baseline:

```bash
oasdiff breaking openapi/baseline/current.json openapi/openapi.json
```

Rules:

- Breaking public `/api/v1` changes fail CI.
- Legacy/internal breaking changes do not block public API checks unless explicitly included.

## 8. CI Sequence

CI MUST run in this order:

```text
1. backend tests
2. frontend tests
3. export OpenAPI
4. Spectral lint
5. Redocly lint
6. Redocly bundle
7. generate frontend transport types
8. frontend typecheck
9. contract fixture tests
10. oasdiff report
```

After stable baseline, step 10 becomes blocking for public `/api/v1` breaking changes.

## 9. Baseline Promotion Rules

- Before the first baseline, `scripts/diff_openapi.sh` must succeed even when `openapi/baseline/current.json` does not exist and must print: `No OpenAPI baseline found; diff is informational only.`
- To promote the first stable baseline, copy `openapi/openapi.json` to `openapi/baseline/current.json` only after Graph, Tables, and Metrics Dashboard pass the migration gate.
- After baseline promotion, breaking-change checks apply only to public `/api/v1` paths unless a future spec expands the public surface.
- Generated frontend types are validation artifacts and implementation inputs. They are not frontend domain models.
