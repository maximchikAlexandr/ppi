/**
 * Pure layout helpers for EntityTreemap. No React, no DOM — the d3
 * treemap pass is an imperative call, but the result is a plain
 * array of leaves the renderer can map over.
 */
import { hierarchy, treemap, treemapSquarify } from "d3-hierarchy";

import type { TreemapItem, TreemapProjection } from "../../../domain/treemap";

export type TreemapLeaf = {
  readonly item: TreemapItem;
  readonly x0: number;
  readonly x1: number;
  readonly y0: number;
  readonly y1: number;
};

export function buildTreemapLeaves(
  projection: TreemapProjection,
  size: { width: number; height: number },
): TreemapLeaf[] {
  if (!projection.items.length) return [];
  type Root = { children: TreemapItem[] };
  const root = hierarchy<Root | TreemapItem>({ children: [...projection.items] })
    .sum((node) => ("size" in node ? Math.max(0, node.size) : 0))
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  return treemap<Root | TreemapItem>()
    .tile(treemapSquarify)
    .size([size.width, size.height])
    .padding(2)(root)
    .leaves()
    .flatMap((leaf) => {
      if (!("size" in leaf.data)) return [];
      const item = leaf.data as TreemapItem;
      return [{ item, x0: leaf.x0, x1: leaf.x1, y0: leaf.y0, y1: leaf.y1 }];
    });
}

/** Distinct groups present in the projection, for the legend. */
export function treemapLegendGroups(
  items: readonly TreemapItem[],
): readonly string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of items) {
    const g = item.group ?? "";
    if (seen.has(g)) continue;
    seen.add(g);
    out.push(g);
  }
  return out;
}

/** Stable hash -> HSL colour, so each group gets a consistent colour. */
export function groupColor(group: string): string {
  if (!group) return "var(--mantine-color-gray-5)";
  let h = 0;
  for (let i = 0; i < group.length; i++) {
    h = (h * 31 + group.charCodeAt(i)) >>> 0;
  }
  const hue = h % 360;
  return `hsl(${hue}, 55%, 55%)`;
}
