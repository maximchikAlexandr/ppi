# API Layer

## Ownership

- `frontend/src/api/generated/**` contains **generated** transport DTOs
  from `openapi-typescript`. These files are owned by the generator
  and must never be hand-edited.
- `frontend/src/api/http.ts` is the typed `openapi-fetch` client
  factory, bound to the generated `paths` types.
- `frontend/src/api/publicApi.ts` is the ONLY public API facade for
  generic frontend code. It consumes the typed `publicHttp` client.
- `frontend/src/api/adapters/**` is the only place that may import
  generated DTOs.

## Forbidden imports in generic code

- `frontend/src/api/generated/**`
- `frontend/src/legacy/**`
- `frontend/src/api/legacyClient.ts` is the legacy `/api/<method>` RPC
  transport. It must only be consumed from `frontend/src/legacy/**` and
  `frontend/src/components/*` (legacy components not yet migrated to
  the generic graph). All generic pages and components must use
  `publicApi.ts` instead.
