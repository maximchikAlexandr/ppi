# Architecture

## Principles

1. **OpenAPI owns transport contract; frontend domain owns rendering primitives.**

   The exported OpenAPI schema (under `openapi/openapi.json`) is the
   single source of truth for HTTP DTOs. The frontend domain types
   (under `frontend/src/domain/`) are owned by the frontend; they are
   not derived from generated DTOs. All public DTOs enter the generic
   frontend through adapters in `frontend/src/api/adapters/**` only.

2. **Backend projections are the only initial generic projection layer.**

   `src/ppi/query/projections.py` returns plain dicts. FastAPI converts
   them to Pydantic response models at the boundary.

3. **Generic code must not branch on concrete Python/Odoo identifiers.**

   Generic components read metric, entity kind, relation type, table,
   graph lens, visual encoding, query, and capability definitions
   through `DefinitionRegistry`. Unknown identifiers render fallback
   labels.

4. **Legacy boundaries are explicit and removable.**

   `frontend/src/legacy/**` and the `frontend/src/registry/odooProfile.ts`
   marker are the only allowed locations for old domain-shaped DTOs and
   labels. Generic code may not import them. A boundary scanner
   (`scripts/check_frontend_boundaries.py`) enforces the rule.
