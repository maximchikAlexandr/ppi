# Frontend API Platform Migration

This document tracks the migration of the dashboard's three main
generic views to the new `/api/v1` public transport.

## Migration gate

The first stable `/api/v1` baseline is declared only when **all three**
of the views below satisfy the migration gate:

- Graph
- Tables
- Metrics Dashboard

A view is migrated when it:

1. Uses `/api/v1` public facade (`publicApi.ts`).
2. Does not call `fetchGraph`, `fetchSnapshotModules`, `fetchSnapshotFiles`,
   `fetchTimeseries`, or `fetchHotspots` directly from generic code.
3. Does not import generated DTOs (`frontend/src/api/generated/**`).
4. Does not read `module_name`, `python_file_count`, `cyclomatic`,
   `cognitive`, `jones`, `manifest_depends`, `model_reuse`,
   `field_property`, `extension_or_method`, `python_lines`,
   `xml_lines`, `score_in`, or `score_out` outside `frontend/src/legacy/**`.
5. Renders only from frontend domain/view models.

## Page migration state matrix

| Page | State | Notes |
|---|---|---|
| Graph | adapted_legacy → public_v1_adapter | Generic data path through `EntityGraph`; legacy wrapper in `ModuleGraph.tsx`. |
| Tables | public_v1_adapter | Generic table renderer in `GenericDataTable`; legacy wrapper `ReportTables`. |
| Metrics Dashboard | public_v1_adapter | `DashboardPage` calls `publicApi` and gates requests on `MetricQueryStateResult.status === "valid"`. |

## Table row action params

`TableRowAction.params` is passed back to
`GET /api/v1/tables/{tableId}` as query parameters when the receiving
table documents those parameters through a `QueryDefinition` or
table-specific metadata. Generic code must not infer `module_name` or
file-specific parameter names from the action itself.

## Legacy adapter status

| Adapter | Status | Removal plan |
|---|---|---|
| `legacyGraphToGenericGraph` | adapted_legacy | delete when `ModuleGraph` is removed |
| `legacySnapshotToGenericTables` | adapted_legacy | delete when `ReportTables` is removed |
| `legacyMetricsToDefinitions` | adapted_legacy | delete when legacy `dashboard_metrics` references are removed |
| `legacyOdooLabels` | legacy | move labels to backend profile metadata; then delete |

## Baseline readiness checklist

- [x] `/api/v1` router mounted.
- [x] Generated TypeScript types present in `frontend/src/api/generated/`.
- [x] `UiConfigProvider` loads the public UI config.
- [x] Graph view renders from `EntityGraph` (generic).
- [x] Tables view renders from `GenericDataTable` (generic).
- [x] Metrics Dashboard issues requests only for `MetricQueryStateResult.status === "valid"`.
- [ ] Human-promoted baseline (`openapi/baseline/current.json`).
