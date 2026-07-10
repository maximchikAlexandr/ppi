# Legacy Boundary

Modules under `frontend/src/legacy/**` are the only place where:

- old domain-shaped DTOs are declared
- adapters convert legacy DTOs to generic domain models

## Allowed imports

Generic frontend code (`frontend/src/api/**`, `frontend/src/domain/**`,
`frontend/src/registry/**`, `frontend/src/components/generic/**`,
`frontend/src/pages/**`) **must not** import from `frontend/src/legacy/**`.

Legacy adapters themselves may import from `frontend/src/legacy/**` and
the typed openapi-fetch client (`frontend/src/api/http.ts` -> publicHttp).

## Removal rules

1. When a generic page no longer reads any legacy DTO field, delete the
   adapter that fed it.
2. When an old endpoint is removed, delete the legacy adapter that
   wrapped it.
3. Keep this directory as small as possible: a file here is a migration
   debt marker, not a permanent home.
