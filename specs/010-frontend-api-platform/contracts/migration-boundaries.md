# Contract: Migration Boundaries

**Feature**: `010-frontend-api-platform`  
**Status**: Hardened draft; implementation not yet complete

## 1. Migration Gate

The first stable `/api/v1` baseline MUST NOT be declared until all of these are true:

1. Graph view uses generated transport access plus explicit domain adapters.
2. Tables view uses generated transport access plus explicit domain adapters.
3. Metrics Dashboard uses generated transport access plus explicit domain adapters.
4. All three views render frontend domain/view models, not raw transport DTOs.
5. All three views pass forbidden identifier checks outside legacy boundaries.

## 2. Allowed Legacy Paths

Legacy DTO fields and old endpoint-specific assumptions are allowed only under:

```text
frontend/src/legacy/**
frontend/src/api/adapters/** when converting from legacy during transition
frontend/src/**/*.fixture.ts
frontend/src/**/*.test.ts when testing legacy adapters
```

## 3. Forbidden Generic Paths

Legacy DTO fields and old endpoint-specific assumptions are forbidden under:

```text
frontend/src/components/generic/**
frontend/src/domain/**
frontend/src/registry/**
frontend/src/visualization/**
frontend/src/pages/** after the page is migrated
```

## 4. Forbidden Identifiers

The validation script MUST search generic paths for these tokens:

```text
module_name
python_file_count
cyclomatic
cognitive
jones
manifest_depends
model_reuse
field_property
extension_or_method
python_lines
xml_lines
score_in
score_out
```

## 5. Stable Baseline Checklist

Before saving `openapi/baseline/current.json`, verify:

- `/api/v1/ui/config` contains definitions required by Graph, Tables, Metrics Dashboard.
- Graph page uses `publicApi.getGraph`.
- Tables page uses `publicApi.getTable` and `publicApi.listTables`.
- Metrics Dashboard uses `publicApi.getMetricTimeseries`, `publicApi.getMetricHotspots`, and `publicApi.listEntities`.
- No migrated page imports `frontend/src/api/generated/**` directly.
- No migrated page imports `frontend/src/legacy/**` directly.
- API lint passes.
- Redocly bundle succeeds.
- Generated transport types compile.
- oasdiff report has been reviewed.

## 6. Page Migration State Matrix

Track each page in `docs/frontend-api-platform-migration.md` using exactly these states:

| Page | State | Allowed API Access | Notes |
|------|-------|--------------------|-------|
| Graph | `legacy`, `adapted_legacy`, `public_v1_adapter`, or `generic_component` | Depends on state | Stable baseline requires `generic_component`. |
| Tables | `legacy`, `adapted_legacy`, `public_v1_adapter`, or `generic_component` | Depends on state | Stable baseline requires `generic_component`. |
| Metrics Dashboard | `legacy`, `adapted_legacy`, `public_v1_adapter`, or `generic_component` | Depends on state | Stable baseline requires `generic_component`. |

State meaning:

- `legacy`: page may use existing legacy client and legacy DTOs.
- `adapted_legacy`: page may use legacy adapters but must not pass raw legacy DTOs to generic components.
- `public_v1_adapter`: page uses `/api/v1` generated transport through `publicApi` and adapters.
- `generic_component`: page receives only domain/view models and passes boundary scanner checks.
