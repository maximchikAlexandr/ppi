# Frontend Migration Plan (Spec 010)

This document tracks legacy artifacts and the conditions for deleting them.
Each row is a migration debt marker, not a permanent home.

## Status legend

- **active**: in use by generic code
- **mid-migration**: in use by generic code but generic replacement exists
- **legacy**: only consumed by exempt legacy code; safe to delete once
  consumers are migrated
- **dead**: no consumers, delete immediately

## Artifacts

| Legacy artifact | Generic replacement | Status | Owner | Delete when |
|-----------------|---------------------|--------|-------|-------------|
| `frontend/src/api/legacyClient.ts` | `frontend/src/api/publicApi.ts` | mid-migration | T094 | `pages/SnapshotPage.tsx` uses `publicApi` for commits |
| `frontend/src/api/legacySchemas.ts` | `frontend/src/api/generated/schema.d.ts` | mid-migration | T094 | All Zod schemas migrated to generated DTOs |
| `frontend/src/legacy/legacySnapshotGraphExplorer.ts` | `frontend/src/components/generic/graph/useEntityGraphExplorer.ts` (TBD) | mid-migration | T095 | `SnapshotPage` consumes generic explorer |
| `frontend/src/legacy/graphUiHelpers.ts` | `frontend/src/visualization/graphSizing.ts` (TBD) | mid-migration | T095 | `ModuleGraph` and `SnapshotPage` use generic sizing |
| `frontend/src/components/ModuleGraph.tsx` | `frontend/src/components/generic/graph/EntityGraph.tsx` | mid-migration | T096 | `SnapshotPage` uses `EntityGraph` directly |
| `frontend/src/components/ModuleDetailPanel.tsx` | `frontend/src/components/EntityDetailPanel.tsx` (TBD) | legacy | T097 | Generic detail panel built from `EntityRef` view model |
| `frontend/src/components/FileTreemap.tsx` | `frontend/src/components/generic/treemap/EntityTreemap.tsx` (TBD) | legacy | T097 | Generic treemap consumes `TreemapProjection` |
| `frontend/src/components/FileDetailPanel.tsx` | `frontend/src/components/generic/treemap/TreemapItemDetailPanel.tsx` (TBD) | legacy | T097 | Generic detail panel |
| `frontend/src/components/GraphSettingsPanel.tsx` | `frontend/src/components/generic/graph/GraphSettingsPanel.tsx` (TBD) | mid-migration | T098 | Panel reads `GraphSettingsViewModel` from registry |
| `frontend/src/components/graphSelectors.ts` | `frontend/src/visualization/graphSelectors.ts` (TBD) | mid-migration | T099 | Pure selectors read `EntityGraphModel` only |
| `frontend/src/components/graphViewModel.ts` | `frontend/src/visualization/graphViewModel.ts` (TBD) | mid-migration | T099 | Pure view model builder reads `EntityGraphModel` only |
| `frontend/src/components/tooltipViewModel.ts` | `frontend/src/components/generic/graph/entityGraphTooltips.ts` | mid-migration | T099 | Tooltip builder uses registry labels only |
| `frontend/src/components/useGraphSettings.ts` | `frontend/src/components/generic/graph/useGraphSettings.ts` (TBD) | mid-migration | T098 | Settings stored as `GraphSettingsViewModel` |
| `frontend/src/utils/snapshotMetrics.ts` | registry metric accessors | legacy | T100 | Generic code never needs raw metric shape |
| `frontend/src/transforms/snapshotTransforms.ts` | `frontend/src/visualization/graphSelection.ts` (TBD) | mid-migration | T099 | Pure functions read `EntityRef` only |
| `frontend/src/transforms/treemapTransforms.ts` | `frontend/src/visualization/treemapTransforms.ts` (TBD) | legacy | T097 | Pure functions read `TreemapProjection` only |
| `frontend/src/legacy/legacyGraphAdapter.ts` | `frontend/src/api/adapters/graphAdapter.ts` | mid-migration | T096 | `SnapshotPage` consumes `EntityGraphModel` directly |
| `frontend/src/legacy/legacyTableAdapter.ts` | `frontend/src/api/adapters/tableAdapter.ts` | mid-migration | T096 | `SnapshotPage` consumes `TableProjection` directly |
| `frontend/src/legacy/legacyTableTransforms.ts` | `frontend/src/components/generic/table/valueRenderers.tsx` | mid-migration | T096 | Generic value renderers handle all cell types |
| `frontend/src/legacy/legacyApiTypes.ts` | `frontend/src/api/generated/schema.d.ts` | legacy | T094 | Replaced by generated DTOs |
| `frontend/src/legacy/analysisResponses.ts` | `frontend/src/registry/__fixtures__/uiConfig.json` | dead | T094 | Consumed only by tests; delete with tests |
| `frontend/src/pages/SnapshotPage.tsx` (legacy graph path) | generic graph composition | mid-migration | T096 | Page consumes `EntityGraph` + `EntityDetailPanel` + `EntityTreemap` |

## Boundary scanner exemptions

`scripts/check_frontend_boundaries.py` lists these files as exempt from
the generic token ban. **Every exemption must reference a row above.**
Add a row before adding an exemption; the scanner will then fail loud
when the migration step is complete.

## Verification

```bash
# Generic code MUST pass all four:
cd frontend
npm run typecheck
npm run check:dead
npm run check:frontend-boundaries
npm run test
```

## Acceptance

- [ ] All P0 review fixes from `ppi_frontend_spec10_review.md` closed.
- [ ] No generic file references `module_name`, `cyclomatic`, `jones`, or
  other domain-shaped identifiers.
- [ ] No generic file imports from `frontend/src/legacy/**`.
- [ ] No generic file uses raw method-string routing
  (`getDataSource().get("…")` or `ds().get("…")`).
- [ ] `SnapshotPage` consumes only `publicApi`, `EntityGraph`,
  `EntityDetailPanel`, `EntityTreemap`.
