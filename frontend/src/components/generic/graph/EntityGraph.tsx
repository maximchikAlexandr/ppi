/**
 * EntityGraph: renders an EntityGraphModel. Reads entity ids from
 * EntityRef; does not branch on legacy Python/Odoo identifiers.
 *
 * Layout is the imperative d3-force simulation; pure node / edge
 * display calculation lives in entityGraphLayout.ts. This component
 * is the shell that wires them together.
 */
import { useMemo, useRef } from "react";
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
};

export function EntityGraph({
  model,
  onSelectNode,
  nodeSizeMetricIds = [],
  nodeColorMetricIds = [],
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
  const viewBox = useMemo(() => {
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
    () => valueScale(model.nodes.map((n) => combinedMetricValue(n, nodeSizeMetricIds))),
    [model.nodes, nodeSizeMetricIds],
  );
  const colorScale = useMemo(
    () => valueScale(model.nodes.map((n) => combinedMetricValue(n, nodeColorMetricIds))),
    [model.nodes, nodeColorMetricIds],
  );

  return (
    <svg
      role="img"
      aria-label="Generic entity graph"
      data-testid="entity-graph"
      ref={svgRef}
      width="100%"
      height={400}
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
              stroke="gray"
              strokeWidth={1}
            />
          );
        })}
        {sim.nodes.map((node) => {
          const p = positions.get(node.id);
          if (!p) return null;
          const original = model.nodes.find((n) => n.entity.id === node.id);
          const tip = registry && original ? buildNodeTooltip(original, registry) : node.entity.label;
          const graphNode = nodeById.get(node.id);
          const sizeValue = graphNode ? combinedMetricValue(graphNode, nodeSizeMetricIds) : null;
          const colorValue = graphNode ? combinedMetricValue(graphNode, nodeColorMetricIds) : null;
          const radius = 8 + sizeScale(sizeValue) * 26;
          const lightness = 42 + colorScale(colorValue) * 28;
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
              style={{ cursor: "grab", touchAction: "none" }}
            >
              <circle r={radius} fill={`hsl(180, 62%, ${lightness}%)`} />
              <text x={0} y={4} textAnchor="middle" fill="white" fontSize={8}>
                {node.entity.label}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );
}

function combinedMetricValue(
  node: EntityGraphModel["nodes"][number],
  metricIds: readonly string[],
): number | null {
  if (!metricIds.length) return null;
  const values = metricIds
    .map((id) => nodeMetricValue(node, id))
    .filter((v): v is number => v !== null);
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function nodeMetricValue(
  node: EntityGraphModel["nodes"][number],
  id: string,
): number | null {
  const [kind, key] = id.split(":", 2);
  const raw = kind === "line"
    ? node.lineCounts?.[key]
    : node.metrics.find((m) => m.metricId === key)?.value;
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
