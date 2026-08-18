/**
 * EntityGraph: renders an EntityGraphModel. Reads entity ids from
 * EntityRef; does not branch on legacy Python/Odoo identifiers.
 *
 * Layout is the imperative d3-force simulation; pure node / edge
 * display calculation lives in entityGraphLayout.ts. This component
 * is the shell that wires them together.
 */
import { ActionIcon, Group, Tooltip } from "@mantine/core";
import { useMemo, useRef, useState } from "react";
import type { PointerEvent } from "react";

import type { EntityGraphModel } from "../../../domain/graph";
import { useUiConfig } from "../../../registry/UiConfigProvider";
import { buildNodeTooltip, buildEdgeTooltip } from "./entityGraphTooltips";
import { useEntityGraphSimulation } from "./useEntityGraphSimulation";

type Props = {
  model: EntityGraphModel;
  onSelectNode?: (entityId: string) => void;
  nodeSizeMetricIds?: readonly string[];
  nodeColorMetricIds?: readonly string[];
  selectedEntityId?: string | null;
};

export function EntityGraph({
  model,
  onSelectNode,
  nodeSizeMetricIds = [],
  nodeColorMetricIds = [],
  selectedEntityId = null,
}: Props) {
  const { registry } = useUiConfig();
  const sim = useEntityGraphSimulation({ model });
  const svgRef = useRef<SVGSVGElement | null>(null);
  const dragRef = useRef<{ nodeId: string; moved: boolean } | null>(null);
  const positions = useMemo(() => {
    const m = new Map<string, { x: number; y: number }>();
    for (const n of sim.nodes) {
      m.set(n.id, { x: n.x ?? 0, y: n.y ?? 0 });
    }
    return m;
  }, [sim.nodes]);
  const [zoom, setZoom] = useState(1);
  const [hoveredEntityId, setHoveredEntityId] = useState<string | null>(null);
  const baseViewBox = useMemo(() => {
    const xs = sim.nodes.map((n) => n.x ?? 0);
    const ys = sim.nodes.map((n) => n.y ?? 0);
    if (!xs.length || !ys.length) return "-240 -200 480 400";
    const pad = 40;
    const minX = Math.min(...xs) - pad;
    const maxX = Math.max(...xs) + pad;
    const minY = Math.min(...ys) - pad;
    const maxY = Math.max(...ys) + pad;
    const width = Math.max(1, maxX - minX);
    const height = Math.max(1, maxY - minY);
    const cappedWidth = Math.min(width, 720);
    const cappedHeight = Math.min(height, 520);
    const centerX = xs.reduce((sum, value) => sum + value, 0) / xs.length;
    const centerY = ys.reduce((sum, value) => sum + value, 0) / ys.length;
    return `${centerX - cappedWidth / 2} ${centerY - cappedHeight / 2} ${cappedWidth} ${cappedHeight}`;
  }, [sim.nodes]);
  const viewBox = useMemo(() => zoomViewBox(baseViewBox, zoom), [baseViewBox, zoom]);

  const lookupTarget = (link: (typeof sim.links)[number]) => {
    const s = typeof link.source === "string" ? sim.nodes.find((n) => n.id === link.source) : link.source;
    const t = typeof link.target === "string" ? sim.nodes.find((n) => n.id === link.target) : link.target;
    return { s, t };
  };
  const nodeById = useMemo(
    () => new Map(model.nodes.map((n) => [n.entity.id, n])),
    [model.nodes],
  );
  const sizeScale = useMemo(
    () => valueScale(model.nodes.map((n) => summedMetricValue(n, nodeSizeMetricIds))),
    [model.nodes, nodeSizeMetricIds],
  );
  const colorScale = useMemo(
    () => valueScale(model.nodes.map((n) => averagedMetricValue(n, nodeColorMetricIds))),
    [model.nodes, nodeColorMetricIds],
  );
  const labeledNodeIds = useMemo(
    () => mostSignificantNodeIds(model, nodeSizeMetricIds, 8),
    [model, nodeSizeMetricIds],
  );

  return (
    <div className="ppi-graph-canvas">
      <Group className="ppi-graph-toolbar" gap={2} aria-label="Graph zoom controls">
        <Tooltip label="Zoom out">
          <ActionIcon
            variant="subtle"
            color="dark"
            aria-label="Zoom out"
            onClick={() => setZoom((value) => Math.max(0.6, value - 0.2))}
          >−</ActionIcon>
        </Tooltip>
        <Tooltip label="Reset zoom">
          <ActionIcon
            variant="subtle"
            color="dark"
            aria-label="Reset zoom"
            style={{ width: 52 }}
            onClick={() => setZoom(1)}
          >{Math.round(zoom * 100)}%</ActionIcon>
        </Tooltip>
        <Tooltip label="Zoom in">
          <ActionIcon
            variant="subtle"
            color="dark"
            aria-label="Zoom in"
            onClick={() => setZoom((value) => Math.min(2.4, value + 0.2))}
          >+</ActionIcon>
        </Tooltip>
      </Group>
      <svg
      role="img"
      aria-label="Generic entity graph"
      data-testid="entity-graph"
      ref={svgRef}
      width="100%"
      height={460}
      viewBox={viewBox}
      onPointerMove={(event) => {
        const drag = dragRef.current;
        if (!drag) return;
        drag.moved = true;
        const point = svgPoint(svgRef.current, event);
        if (!point) return;
        sim.dragMove(drag.nodeId, point.x, point.y);
      }}
      onPointerUp={(event) => {
        const drag = dragRef.current;
        if (!drag) return;
        sim.dragEnd(drag.nodeId);
        if (!drag.moved) onSelectNode?.(drag.nodeId);
        dragRef.current = null;
        if (event.currentTarget.hasPointerCapture(event.pointerId)) {
          event.currentTarget.releasePointerCapture(event.pointerId);
        }
      }}
      onPointerCancel={() => {
        const drag = dragRef.current;
        if (!drag) return;
        sim.dragEnd(drag.nodeId);
        dragRef.current = null;
      }}
      onLostPointerCapture={() => {
        const drag = dragRef.current;
        if (!drag) return;
        sim.dragEnd(drag.nodeId);
        dragRef.current = null;
      }}
    >
      <g>
        {sim.links.map((link) => {
          const { s, t } = lookupTarget(link);
          if (!s || !t) return null;
          const x1 = s.x ?? 0;
          const y1 = s.y ?? 0;
          const x2 = t.x ?? 0;
          const y2 = t.y ?? 0;
          const tip = registry ? buildEdgeTooltip(link.edge, registry) : "";
          return (
            <line
              key={link.id}
              data-testid="graph-edge"
              data-tip={tip}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#9aabc0"
              strokeOpacity={0.58}
              strokeWidth={1.15}
            />
          );
        })}
        {sim.nodes.map((node) => {
          const p = positions.get(node.id);
          if (!p) return null;
          const original = model.nodes.find((n) => n.entity.id === node.id);
          const tip = registry && original ? buildNodeTooltip(original, registry) : node.entity.label;
          const graphNode = nodeById.get(node.id);
          const sizeValue = graphNode ? summedMetricValue(graphNode, nodeSizeMetricIds) : null;
          const colorValue = graphNode ? averagedMetricValue(graphNode, nodeColorMetricIds) : null;
          const radius = 8 + sizeScale(sizeValue) * 26;
          const lightness = 42 + colorScale(colorValue) * 28;
          const selected = selectedEntityId === node.id;
          return (
            <g
              key={node.id}
              data-testid="graph-node"
              data-tip={tip}
              transform={`translate(${p.x},${p.y})`}
              onPointerDown={(event) => {
                event.preventDefault();
                event.stopPropagation();
                const point = svgPoint(svgRef.current, event);
                if (!point) return;
                dragRef.current = { nodeId: node.id, moved: false };
                event.currentTarget.ownerSVGElement?.setPointerCapture(event.pointerId);
                sim.dragStart(node.id, point.x, point.y);
              }}
              onPointerEnter={() => setHoveredEntityId(node.id)}
              onPointerLeave={() => setHoveredEntityId((current) => current === node.id ? null : current)}
              style={{ cursor: "grab", touchAction: "none" }}
            >
              <title>{tip}</title>
              <circle
                r={radius}
                fill={`hsl(183, 58%, ${lightness}%)`}
                stroke={selected ? "#173f65" : "rgba(255,255,255,.9)"}
                strokeWidth={selected ? 4 : 1.5}
                style={{ filter: "drop-shadow(0 3px 5px rgba(34,67,91,.18))" }}
              />
              {sizeValue !== null ? (
                <text
                  x={0}
                  y={4}
                  textAnchor="middle"
                  fill="#10243a"
                  fontSize={Math.max(8, Math.min(12, radius * 0.5))}
                  fontWeight={800}
                  pointerEvents="none"
                  style={{ paintOrder: "stroke", stroke: "rgba(255,255,255,.82)", strokeWidth: 1.5 }}
                >
                  {formatCompactNumber(sizeValue)}
                </text>
              ) : null}
              {selected || hoveredEntityId === node.id || labeledNodeIds.has(node.id) ? (
                <text
                  x={0}
                  y={radius + 13}
                  textAnchor="middle"
                  fill="#203047"
                  fontSize={selected ? 9 : 8}
                  fontWeight={selected ? 750 : 600}
                  style={{ paintOrder: "stroke", stroke: "#fbfcff", strokeWidth: 4 }}
                >
                  {node.entity.label}
                </text>
              ) : null}
            </g>
          );
        })}
      </g>
      </svg>
    </div>
  );
}

function mostSignificantNodeIds(
  model: EntityGraphModel,
  metricIds: readonly string[],
  limit: number,
): ReadonlySet<string> {
  const degree = new Map<string, number>();
  for (const edge of model.edges) {
    degree.set(edge.source.id, (degree.get(edge.source.id) ?? 0) + 1);
    degree.set(edge.target.id, (degree.get(edge.target.id) ?? 0) + 1);
  }
  return new Set(
    [...model.nodes]
      .sort((a, b) => {
        const aMetric = summedMetricValue(a, metricIds);
        const bMetric = summedMetricValue(b, metricIds);
        return (bMetric ?? degree.get(b.entity.id) ?? 0) - (aMetric ?? degree.get(a.entity.id) ?? 0);
      })
      .slice(0, limit)
      .map((node) => node.entity.id),
  );
}

function zoomViewBox(viewBox: string, zoom: number): string {
  const [x, y, width, height] = viewBox.split(" ").map(Number);
  if (![x, y, width, height].every(Number.isFinite)) return viewBox;
  const nextWidth = width / zoom;
  const nextHeight = height / zoom;
  return `${x + (width - nextWidth) / 2} ${y + (height - nextHeight) / 2} ${nextWidth} ${nextHeight}`;
}

function summedMetricValue(
  node: EntityGraphModel["nodes"][number],
  metricIds: readonly string[],
): number | null {
  if (!metricIds.length) return null;
  const values = metricIds
    .map((id) => nodeMetricValue(node, id))
    .filter((v): v is number => v !== null);
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0);
}

function averagedMetricValue(
  node: EntityGraphModel["nodes"][number],
  metricIds: readonly string[],
): number | null {
  const sum = summedMetricValue(node, metricIds);
  if (sum === null) return null;
  const count = metricIds.reduce(
    (total, id) => total + (nodeMetricValue(node, id) === null ? 0 : 1),
    0,
  );
  return count ? sum / count : null;
}

function nodeMetricValue(
  node: EntityGraphModel["nodes"][number],
  id: string,
): number | null {
  const [kind, key, aggregation] = id.split(":", 3);
  const raw = kind === "line"
    ? node.lineCounts?.[key]
    : node.metrics.find(
      (m) => m.metricId === key && (aggregation === undefined || m.aggregation === aggregation),
    )?.value;
  return typeof raw === "number" && Number.isFinite(raw) ? raw : null;
}

function valueScale(values: readonly (number | null)[]): (value: number | null) => number {
  const numeric = values.filter((v): v is number => v !== null && Number.isFinite(v));
  if (!numeric.length) return () => 0;
  const min = Math.min(...numeric);
  const max = Math.max(...numeric);
  if (max <= min) return (value) => (value === null ? 0 : 0.5);
  return (value) => {
    if (value === null) return 0;
    return Math.max(0, Math.min(1, (value - min) / (max - min)));
  };
}

function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat(undefined, {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function svgPoint(
  svg: SVGSVGElement | null,
  event: PointerEvent,
): { x: number; y: number } | null {
  if (!svg) return null;
  const point = svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  const matrix = svg.getScreenCTM();
  if (!matrix) return null;
  const transformed = point.matrixTransform(matrix.inverse());
  return { x: transformed.x, y: transformed.y };
}
