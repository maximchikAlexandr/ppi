# Frontend Migration Plan (Spec 010)

This document tracks legacy artifacts and the conditions for deleting them.
Each row is a migration debt marker, not a permanent home.

## Status legend

- **active**: in use by generic code
- **mid-migration**: in use by generic code but generic replacement exists
- **legacy**: only consumed by exempt legacy code; safe to delete once
  consumers are migrated
- **done**: generic replacement has shipped, legacy file deleted

## Artifacts

| Legacy artifact | Generic replacement | Status | Owner | Notes |
|-----------------|---------------------|--------|-------|-------|
| `frontend/src/api/legacyClient.ts` | (deleted) | done | T094 | Zero importers; deleted in iter 3 |
| `frontend/src/api/legacySchemas.ts` | `frontend/src/api/generated/schema.d.ts` | kept | T094 | `apiProtocol.ts` decodes the webview envelope; new code uses generated DTOs |
| `frontend/src/legacy/` (folder) | — | done | T094-T100 | ModuleGraph, FileTreemap, FileDetailPanel, ModuleDetailPanel, GraphSettingsPanel, graphSelectors, graphViewModel, tooltipViewModel, useGraphSettings, useGraphLayoutStore, graphPersistence, graphSettingsTypes, VisibleLinesSummary, legacySnapshotGraphExplorer, legacyGraphAdapter, legacyTableAdapter, legacyTableTransforms, legacyApiTypes, analysisResponses, snapshotTransforms, treemapTransforms, snapshotMetrics, graphViewPure — all deleted |
| `frontend/src/transforms/snapshotTransforms.ts` | inline in `pages/SnapshotPage.tsx` | done | T099 | commitPositionLabel / resolveGraphSelection folded into the page |
| `frontend/src/transforms/treemapTransforms.ts` | `frontend/src/components/generic/treemap/entityTreemapLayout.ts` | done | T097 | Pure treemap helpers moved to the generic component |
| `frontend/src/utils/snapshotMetrics.ts` | registry metric accessors | done | T100 | No consumer; deleted |
| `frontend/src/components/GraphSettingsPanel.tsx` | `frontend/src/components/generic/graph/GenericGraphSettingsBar.tsx` | done | T098 | Only the line-category filter is needed today; the legacy 660-line panel is gone |
| `frontend/src/components/ModuleGraph.tsx` | `frontend/src/components/generic/graph/EntityGraph.tsx` | done | T096 | Generic graph with `useEntityGraphSimulation` shell |
| `frontend/src/components/FileTreemap.tsx` | `frontend/src/components/generic/treemap/EntityTreemap.tsx` | done | T097 | Driven by `TreemapProjection` |
| `frontend/src/components/FileDetailPanel.tsx` | `frontend/src/components/generic/treemap/TreemapItemDetailPanel.tsx` | done | T097 | Renders `metricGroups` chips; no fixed metric ids |
| `frontend/src/components/ModuleDetailPanel.tsx` | inline `TreemapItemDetailPanel` | done | T097 | Old `module_name` panel deleted |
| `frontend/src/components/graphSelectors.ts` | selectors removed (graph has no filter pipeline yet) | done | T099 | New `EntityGraph` does not need a selector pass; the data shape is small enough to render directly |
| `frontend/src/components/graphViewModel.ts` | `frontend/src/components/generic/graph/entityGraphLayout.ts` | done | T099 | Layout helpers live next to the generic component |
| `frontend/src/components/tooltipViewModel.ts` | `frontend/src/components/generic/graph/entityGraphTooltips.ts` | done | T099 | Tooltip builder uses registry labels only |
| `frontend/src/legacy/legacySnapshotGraphExplorer.ts` | page-owned state in `pages/SnapshotPage.tsx` | done | T095 | 308-line god-hook deleted |
| `frontend/src/legacy/legacyGraphAdapter.ts` | `frontend/src/api/adapters/graphAdapter.ts` | done | T094 | Adapter is the source of truth |
| `frontend/src/legacy/legacyTableAdapter.ts` | `frontend/src/api/adapters/tableAdapter.ts` | done | T094 | Same |
| `frontend/src/legacy/legacyTableTransforms.test.ts` | `frontend/src/components/generic/values/` (Boolean/Date/Generic/Metric/Number) | done | T096 | Old test deleted; generic renderers are tested separately |
| `frontend/src/legacy/legacyApiTypes.ts` | `frontend/src/api/generated/schema.d.ts` | done | T094 | Hand-rolled snake_case types deleted |
| `frontend/src/legacy/analysisResponses.ts` | `frontend/src/registry/__fixtures__/unknownUiConfig.ts` | done | T094 | Consumed only by tests; both fixtures and tests gone |

## Generic platform (intentional, not migration debt)

These files are part of the new generic platform. They are exempt from
the boundary scanner because they are transport shells (encode/decode,
HTTP, webview bridge). Do not remove without discussion.

- `frontend/src/api/publicApi.ts` — typed `openapi-fetch` facade; the
  only public API surface for generic code.
- `frontend/src/api/http.ts` — `openapi-fetch` factory bound to
  generated `paths` types.
- `frontend/src/api/apiProtocol.ts` — RPC envelope / URL encoding
  shared by webview and HTTP transports.
- `frontend/src/api/dataSource.ts` — `HttpDataSource` and
  `WebviewDataSource` shells; the IO boundary.
- `frontend/src/api/adapters/` — DTO -> domain adapters; the only
  place that may import generated DTOs.
- `frontend/src/api/generated/` — auto-generated DTOs; never hand-edit.
- `frontend/src/api/legacySchemas.ts`
  — kept for the webview RPC envelope (apiProtocol uses
  `ResponseEnvelopeSchema` to decode the webview's response
  frames). The boundary scanner exempts the file; generic
  pages do not import it. The file still holds the legacy
  snake_case Zod shapes for the `/api/<method>` envelope; no
  page or adapter references its types any more.
- `frontend/src/legacy/` (folder) — empty; the folder is kept so the
  `frontend/src/legacy/**` exemption prefix remains a stable contract.
  Future exemptions for legacy adapters land here.

## Verification

```bash
# Generic code MUST pass all four:
cd frontend
npm run typecheck
npm run check:dead
npm run check:frontend-boundaries
npm run test

# Scanner self-test (smoke):
cd ..
make api-boundaries
```

## Acceptance

- [x] All P0 review fixes from `ppi_frontend_spec10_review.md` closed.
- [x] P1 EntityGraph, generic DataTable, UiConfigProvider, odooProfile,
  treemap/detail, RemoteData, contract fixtures.
- [ ] P2: remove unused dependencies, tighten code-size budget, declare
  `/api/v1` stable baseline.

## Test counts after P1

- `npm run test`: 129 tests across 20 files.
- `make api-boundaries`: 7 self-test cases + boundary OK.
- `uv run pytest tests/server/`: 40 passed.
