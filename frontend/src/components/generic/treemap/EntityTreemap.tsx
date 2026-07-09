/**
 * EntityTreemap: renders a TreemapProjection. The page owns the
 * selection and the drilldown stack; this component just emits
 * actions. No entity-name or metric-id special cases — every chip
 * comes from the projection's metricGroups.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Stack, Text } from "@mantine/core";

import { compactLines } from "../../../utils/metricFormat";
import {
  buildTreemapLeaves,
  groupColor,
  treemapLegendGroups,
  type TreemapLeaf,
} from "./entityTreemapLayout";
import type { EntityId } from "../../../domain/ids";
import type { TreemapItem, TreemapProjection } from "../../../domain/treemap";

type Props = {
  readonly projection: TreemapProjection;
  readonly selectedId?: EntityId | null;
  readonly onSelect?: (itemId: EntityId) => void;
  readonly onHover?: (itemId: EntityId | null) => void;
};

const TRUNCATE = (text: string, max: number): string =>
  text.length <= max ? text : `${text.slice(0, Math.max(0, max - 1))}…`;
const MIN_TEXT_W = 36;
const MIN_TEXT_H = 18;

export function EntityTreemap({ projection, selectedId, onSelect, onHover }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const size = useContainerSize(containerRef);
  const legend = useMemo(() => treemapLegendGroups(projection.items), [projection.items]);
  const leaves = useMemo(
    () => buildTreemapLeaves(projection, { width: size.width, height: size.height }),
    [projection, size.height, size.width],
  );

  if (!projection.items.length) {
    return (
      <div ref={containerRef} style={{ padding: 24 }}>
        <Text size="sm" c="dimmed">
          {projection.title ? `${projection.title}: no items.` : "No items."}
        </Text>
      </div>
    );
  }

  return (
    <Stack gap="xs" ref={containerRef}>
      <Text fw={600}>{projection.title}</Text>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        {legend.map((group) => (
          <span key={group || "default"} style={{ fontSize: 12 }}>
            <span
              style={{
                display: "inline-block",
                width: 12,
                height: 12,
                background: groupColor(group),
                marginRight: 4,
              }}
            />
            {group || "default"}
          </span>
        ))}
      </div>
      <svg
        width="100%"
        height={size.height}
        viewBox={`0 0 ${size.width} ${size.height}`}
        style={{
          border: "1px solid var(--mantine-color-gray-3)",
          background: "#fbfcfd",
          display: "block",
        }}
        data-testid="entity-treemap"
      >
        {leaves.map((leaf) => (
          <TreemapTile
            key={leaf.item.entity.id}
            leaf={leaf}
            selected={selectedId === leaf.item.entity.id}
            onSelect={onSelect}
            onHover={onHover}
          />
        ))}
      </svg>
    </Stack>
  );
}

function TreemapTile({
  leaf,
  selected,
  onSelect,
  onHover,
}: {
  leaf: TreemapLeaf;
  selected: boolean;
  onSelect?: (id: EntityId) => void;
  onHover?: (id: EntityId | null) => void;
}) {
  const innerW = leaf.x1 - leaf.x0;
  const innerH = leaf.y1 - leaf.y0;
  const centerX = innerW / 2;
  const centerY = innerH / 2;
  const maxChars = Math.max(0, Math.floor((innerW - 6) / 6.8));
  const displayName = TRUNCATE(leaf.item.entity.label, maxChars);
  const displaySize = TRUNCATE(compactLines(leaf.item.size), maxChars);
  const fill = leaf.item.colorMetricId
    ? groupColor(`${leaf.item.colorMetricId}:${Math.round(leaf.item.colorValue ?? 0)}`)
    : groupColor(leaf.item.group ?? "");
  return (
    <g
      transform={`translate(${leaf.x0}, ${leaf.y0})`}
      onClick={() => onSelect?.(leaf.item.entity.id)}
      onMouseEnter={() => onHover?.(leaf.item.entity.id)}
      onMouseLeave={() => onHover?.(null)}
      style={{ cursor: "pointer" }}
      data-testid="treemap-tile"
      data-entity-id={leaf.item.entity.id}
    >
      <title>{buildTooltip(leaf.item)}</title>
      <rect
        width={innerW}
        height={innerH}
        fill={fill}
        stroke={selected ? "#228be6" : "#fff"}
        strokeWidth={selected ? 2 : 1}
      />
      {innerW >= MIN_TEXT_W && innerH >= MIN_TEXT_H ? (
        <>
          {displayName ? (
            <text
              x={centerX}
              y={displaySize ? centerY - 2 : centerY + 4}
              textAnchor="middle"
              fontSize={12}
              fontWeight={600}
              fill="#ffffff"
              pointerEvents="none"
            >
              {displayName}
            </text>
          ) : null}
          {displaySize ? (
            <text
              x={centerX}
              y={displayName ? centerY + 14 : centerY + 4}
              textAnchor="middle"
              fontSize={12}
              fill="#ffffff"
              pointerEvents="none"
            >
              {displaySize}
            </text>
          ) : null}
        </>
      ) : null}
    </g>
  );
}

function buildTooltip(item: TreemapItem): string {
  const head = `${item.entity.kind}: ${item.entity.label}\nsize=${item.size}`;
  const chips = item.metricGroups
    .filter((g) => g.value !== null)
    .map((g) => `${g.label}=${g.value}`)
    .join(" ");
  return chips ? `${head}\n${chips}` : head;
}

function useContainerSize(ref: React.RefObject<HTMLDivElement | null>) {
  const [size, setSize] = useState({ width: 860, height: 560 });
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      setSize({ width: Math.max(320, Math.floor(entry.contentRect.width)), height: 560 });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, [ref]);
  return size;
}
