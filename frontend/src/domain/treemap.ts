import type { EntityId, EntityKindId, MetricId } from "./ids";
import type { ValueFormat } from "./metric";

/**
 * TreemapItem — a generic leaf in a treemap, decoupled from
 * module/file/Odoo semantics. The size metric drives the tile area;
 * the color metric drives the tile fill (resolved by the consumer
 * using a visual encoding). metricGroups and attributes are the
 * "metric chips" and arbitrary key/value pairs shown in the detail
 * panel.
 */
export type TreemapItem = {
  readonly entity: {
    readonly id: EntityId;
    readonly kind: EntityKindId;
    readonly label: string;
    readonly path?: string | null;
  };
  /** A non-negative number driving the tile area. */
  readonly size: number;
  /** Optional metric id used to colour the tile. */
  readonly colorMetricId?: MetricId | null;
  /** Optional metric value driving the colour (already aggregated). */
  readonly colorValue?: number | null;
  /** Group label, used for legend chips. */
  readonly group?: string | null;
  /** Metric values surfaced as chips in the detail panel. */
  readonly metricGroups: ReadonlyArray<{
    readonly id: MetricId;
    readonly label: string;
    readonly value: number | string | null;
    readonly unit?: string | null;
    readonly format?: ValueFormat | null;
  }>;
  /** Free-form attributes (line counts, paths, etc.). */
  readonly attributes: Readonly<Record<string, string | number | null>>;
};

/**
 * TreemapProjection — what a page passes to a generic
 * EntityTreemap. The adapter (api/adapters/treemapAdapter.ts) builds
 * this from a `/api/v1/treemap` response or from a table projection
 * that has a `size` column.
 */
export type TreemapProjection = {
  readonly title: string;
  readonly items: readonly TreemapItem[];
  /** Default selection when the treemap first renders. */
  readonly defaultSelectedId?: EntityId | null;
};

/** Action emitted when a leaf is clicked. Pages translate this into a
 * drilldown via DefinitionRegistry. */
export type TreemapAction =
  | { readonly kind: "select"; readonly itemId: EntityId }
  | { readonly kind: "drilldown"; readonly itemId: EntityId };
