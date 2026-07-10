import { describe, expect, it } from "vitest";
import React from "react";
import { render } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";

import { EntityTreemap } from "./EntityTreemap";
import { TreemapItemDetailPanel } from "./TreemapItemDetailPanel";
import type { TreemapProjection, TreemapItem } from "../../../domain/treemap";

function makeItem(over: Partial<TreemapItem> & { id: string; size?: number }): TreemapItem {
  const { id, size = 100, ...rest } = over;
  return {
    entity: { id: id as never, kind: "module" as never, label: id },
    size,
    metricGroups: rest.metricGroups ?? [
      { id: "lines", label: "Lines", value: size, unit: null, format: null },
    ],
    attributes: rest.attributes ?? {},
    group: rest.group ?? null,
    colorMetricId: rest.colorMetricId ?? null,
    colorValue: rest.colorValue ?? null,
  };
}

const sample: TreemapProjection = {
  title: "Sample treemap",
  items: [
    makeItem({ id: "alpha", size: 200 }),
    makeItem({ id: "beta", size: 100, group: "core" }),
    makeItem({ id: "gamma", size: 50, group: "core" }),
  ],
};

function wrap(node: React.ReactNode) {
  return <MantineProvider>{node}</MantineProvider>;
}

describe("EntityTreemap", () => {
  it("renders one tile per item", () => {
    const { container } = render(wrap(<EntityTreemap projection={sample} />));
    const tiles = container.querySelectorAll('[data-testid="treemap-tile"]');
    expect(tiles).toHaveLength(3);
  });

  it("emits select on click", () => {
    let clicked: string | null = null;
    const { container } = render(
      wrap(
        <EntityTreemap
          projection={sample}
          onSelect={(id) => {
            clicked = id;
          }}
        />,
      ),
    );
    const tile = container.querySelector('[data-entity-id="alpha"]') as SVGGElement;
    tile.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(clicked).toBe("alpha");
  });

  it("renders an empty state when there are no items", () => {
    const { container } = render(
      wrap(<EntityTreemap projection={{ title: "Empty", items: [] }} />),
    );
    expect(container.querySelector('[data-testid="entity-treemap"]')).toBeNull();
  });
});

describe("TreemapItemDetailPanel", () => {
  it("renders metric chips and never reads cyclomatic / jones", () => {
    const item = makeItem({
      id: "alpha",
      size: 200,
      metricGroups: [
        { id: "fremium_score", label: "Fremium Score", value: 73, unit: null, format: null },
        { id: "fremium_pct", label: "Fremium %", value: 0.42, unit: null, format: null },
      ],
    });
    const { container } = render(wrap(<TreemapItemDetailPanel item={item} />));
    expect(container.textContent).toContain("Fremium Score");
    expect(container.textContent).toContain("Fremium %");
    expect(container.textContent).not.toContain("cyclomatic");
    expect(container.textContent).not.toContain("jones");
    expect(container.textContent).not.toContain("module_name");
  });

  it("renders the empty hint when no item is selected", () => {
    const { container } = render(
      wrap(
        <TreemapItemDetailPanel
          item={null}
          emptyLabel="Pick something."
        />,
      ),
    );
    expect(container.textContent).toContain("Pick something.");
  });
});
