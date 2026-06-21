import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from "d3-force";
import { Button, Group, Text } from "@mantine/core";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { GraphEdge, GraphNode } from "../api/client";
import {
  computeNodeBrightnessMap,
  computeNodeRadiusMap,
  colorForComplexityRatio,
  lineCategoryTotal,
  MIN_NODE_RADIUS,
  NEUTRAL_NODE_RADIUS,
  strokeForComplexityRatio,
  textColorForComplexityRatio,
  type BrightnessCriterion,
  type LineCategoryKey,
} from "../registry/odooProfile";
import { formatCodeLines, formatMetricValue } from "../utils/metricFormat";

type SimNode = SimulationNodeDatum & {
  id: string;
  node: GraphNode;
  radius: number;
};

type SimLink = SimulationLinkDatum<SimNode> & {
  edge: GraphEdge;
  offset: number;
};

type ViewBox = {
  x: number;
  y: number;
  w: number;
  h: number;
};

type Props = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  lineCategories: Set<LineCategoryKey>;
  brightnessCriteria: Set<BrightnessCriterion>;
  selectedModule: string | null;
  onSelectModule: (name: string | null) => void;
  loading?: boolean;
};

const WIDTH = 1600;
const HEIGHT = 860;
const MIN_EDGE_STROKE = 0.9;
const MAX_EDGE_STROKE = 3;
const CAMERA_PADDING = 140;
const CAMERA_LERP = 0.18;
const ZOOM_MIN = 0.35;
const ZOOM_MAX = 8;
const ZOOM_STEP = 1.18;
const INITIAL_VIEWBOX = `0 0 ${WIDTH} ${HEIGHT}`;

function edgeStrokeWidth(points: number): number {
  return MIN_EDGE_STROKE + Math.min(MAX_EDGE_STROKE - MIN_EDGE_STROKE, Math.max(points, 0) / 18);
}

function buildEdgeTooltip(edge: GraphEdge): string {
  return [
    `${edge.source} -> ${edge.target}`,
    `points=${edge.breakdown.total}`,
    `reuse=${edge.breakdown.model_reuse}`,
    `extend/method=${edge.breakdown.extension_or_method}`,
    `view=${edge.breakdown.view}`,
    `field/property=${edge.breakdown.field_property}`,
  ].join(" | ");
}

function buildNodeTooltip(node: GraphNode, visible: number): string {
  return [
    node.module_name,
    `visible=${formatCodeLines(visible)}`,
    `CC med ${formatMetricValue(node.cyclomatic_median)}`,
    `cognitive med ${formatMetricValue(node.cognitive_median)}`,
    `Jones med ${formatMetricValue(node.jones_median)}`,
    `methods=${node.method_count}`,
  ].join(" | ");
}

function linkEndpointId(value: string | number | SimNode): string {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number") {
    return String(value);
  }
  return value.id;
}

function edgeCurvePath(
  source: { x: number; y: number; radius: number },
  target: { x: number; y: number; radius: number },
  offset: number,
): string {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const dist = Math.hypot(dx, dy) || 1;
  const ux = dx / dist;
  const uy = dy / dist;
  const nx = -uy;
  const ny = ux;
  const startX = source.x + ux * (source.radius + 1.5);
  const startY = source.y + uy * (source.radius + 1.5);
  const endX = target.x - ux * (target.radius + 4);
  const endY = target.y - uy * (target.radius + 4);
  const curve = offset;
  const cx = (startX + endX) / 2 + nx * curve;
  const cy = (startY + endY) / 2 + ny * curve;
  return `M ${startX} ${startY} Q ${cx} ${cy} ${endX} ${endY}`;
}

function clamp(value: number, low: number, high: number): number {
  return Math.max(low, Math.min(high, value));
}

function computeTargetViewBox(
  positions: Map<string, { x: number; y: number; radius: number }>,
  zoomScale: number,
  manualPanX: number,
  manualPanY: number,
): ViewBox {
  if (!positions.size) {
    return { x: 0, y: 0, w: WIDTH, h: HEIGHT };
  }
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  let maxRadius = MIN_NODE_RADIUS;
  for (const point of positions.values()) {
    minX = Math.min(minX, point.x - point.radius);
    maxX = Math.max(maxX, point.x + point.radius);
    minY = Math.min(minY, point.y - point.radius);
    maxY = Math.max(maxY, point.y + point.radius);
    maxRadius = Math.max(maxRadius, point.radius);
  }
  const padding = maxRadius + CAMERA_PADDING;
  let targetX = minX - padding;
  let targetY = minY - padding;
  let targetW = Math.max(WIDTH, maxX - minX + padding * 2);
  let targetH = Math.max(HEIGHT, maxY - minY + padding * 2);
  if (targetW === WIDTH) {
    targetX = (minX + maxX) / 2 - targetW / 2;
  }
  if (targetH === HEIGHT) {
    targetY = (minY + maxY) / 2 - targetH / 2;
  }
  const centerX = targetX + targetW / 2;
  const centerY = targetY + targetH / 2;
  targetW /= zoomScale;
  targetH /= zoomScale;
  targetX = centerX - targetW / 2 + manualPanX;
  targetY = centerY - targetH / 2 + manualPanY;
  return { x: targetX, y: targetY, w: targetW, h: targetH };
}

export function ModuleGraph({
  nodes,
  edges,
  lineCategories,
  brightnessCriteria,
  selectedModule,
  onSelectModule,
  loading = false,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<Simulation<SimNode, SimLink> | null>(null);
  const nodesRef = useRef<SimNode[]>([]);
  const simLinksRef = useRef<SimLink[]>([]);
  const linkPathRefs = useRef<Map<string, SVGPathElement>>(new Map());
  const nodeGroupRefs = useRef<Map<string, SVGGElement>>(new Map());
  const positionsRef = useRef<Map<string, { x: number; y: number; radius: number }>>(new Map());
  const viewBoxRef = useRef<ViewBox>({ x: 0, y: 0, w: WIDTH, h: HEIGHT });
  const radiusByIdRef = useRef<Map<string, number>>(new Map());
  const zoomScaleRef = useRef(1);
  const manualPanRef = useRef({ x: 0, y: 0 });
  const [zoomLabel, setZoomLabel] = useState(100);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [panning, setPanning] = useState<{ startX: number; startY: number; panX: number; panY: number } | null>(
    null,
  );

  const brightnessById = useMemo(
    () => computeNodeBrightnessMap(nodes, brightnessCriteria),
    [brightnessCriteria, nodes],
  );

  const radiusById = useMemo(
    () => computeNodeRadiusMap(nodes, lineCategories),
    [lineCategories, nodes],
  );

  useEffect(() => {
    radiusByIdRef.current = radiusById;
  }, [radiusById]);

  const simNodes: SimNode[] = useMemo(
    () =>
      nodes.map((node) => ({
        id: node.module_name,
        node,
        radius: radiusById.get(node.module_name) ?? NEUTRAL_NODE_RADIUS,
      })),
    [nodes, radiusById],
  );

  const simLinks: SimLink[] = useMemo(() => {
    const edgeKeys = new Set(edges.map((edge) => `${edge.source}|${edge.target}`));
    return edges.map((edge) => {
      const reverse = edgeKeys.has(`${edge.target}|${edge.source}`);
      const offset = reverse && edge.source > edge.target ? 18 : reverse ? -18 : 0;
      return {
        source: edge.source,
        target: edge.target,
        edge,
        offset,
      };
    });
  }, [edges]);

  useEffect(() => {
    simLinksRef.current = simLinks;
  }, [simLinks]);

  const nodeSignature = useMemo(
    () => nodes.map((node) => node.module_name).join(","),
    [nodes],
  );

  const syncGraphDom = useCallback((layoutNodes: SimNode[]) => {
    const positions = new Map(
      layoutNodes.map((node) => [
        node.id,
        { x: node.x ?? 0, y: node.y ?? 0, radius: node.radius },
      ]),
    );
    positionsRef.current = positions;
    for (const link of simLinksRef.current) {
      const sourceId = linkEndpointId(link.source);
      const targetId = linkEndpointId(link.target);
      const key = `${sourceId}-${targetId}-${link.offset}`;
      const pathEl = linkPathRefs.current.get(key);
      const source = positions.get(sourceId);
      const target = positions.get(targetId);
      if (!pathEl || !source || !target) {
        continue;
      }
      const sourceRadius = source.radius || radiusByIdRef.current.get(sourceId) || MIN_NODE_RADIUS;
      const targetRadius = target.radius || radiusByIdRef.current.get(targetId) || MIN_NODE_RADIUS;
      pathEl.setAttribute(
        "d",
        edgeCurvePath(
          { x: source.x, y: source.y, radius: sourceRadius },
          { x: target.x, y: target.y, radius: targetRadius },
          link.offset,
        ),
      );
    }
    for (const node of layoutNodes) {
      const group = nodeGroupRefs.current.get(node.id);
      if (group) {
        group.setAttribute("transform", `translate(${node.x ?? 0}, ${node.y ?? 0})`);
      }
    }
  }, []);

  useEffect(() => {
    zoomScaleRef.current = 1;
    manualPanRef.current = { x: 0, y: 0 };
    setZoomLabel(100);
    const layoutNodes: SimNode[] = nodes.map((node) => ({
      id: node.module_name,
      node,
      radius: radiusByIdRef.current.get(node.module_name) ?? NEUTRAL_NODE_RADIUS,
      x: WIDTH / 2 + (Math.random() - 0.5) * 80,
      y: HEIGHT / 2 + (Math.random() - 0.5) * 80,
      vx: (Math.random() - 0.5) * 2,
      vy: (Math.random() - 0.5) * 2,
    }));
    nodesRef.current = layoutNodes;

    simulationRef.current?.stop();
    const simulation = forceSimulation(layoutNodes)
      .force(
        "link",
        forceLink<SimNode, SimLink>(simLinks)
          .id((node) => node.id)
          .distance((link) => Math.max(40, 200 - Math.min(18, link.edge.breakdown.total * 0.9)))
          .strength((link) => Math.min(1, 0.15 + link.edge.breakdown.total * 0.05)),
      )
      .force("charge", forceManyBody().strength(-900))
      .force("center", forceCenter(WIDTH / 2, HEIGHT / 2).strength(0.05))
      .force(
        "collide",
        forceCollide<SimNode>().radius((node) => node.radius + 6),
      )
      .velocityDecay(0.88)
      .alphaDecay(0.015)
      .alphaMin(0.001)
      .alphaTarget(0.02);

    simulation.on("tick", () => {
      syncGraphDom(layoutNodes);
    });

    simulationRef.current = simulation;
    syncGraphDom(layoutNodes);
    const syncFrame = requestAnimationFrame(() => syncGraphDom(layoutNodes));
    return () => {
      cancelAnimationFrame(syncFrame);
      simulation.stop();
      simulationRef.current = null;
    };
  }, [nodeSignature, simLinks, syncGraphDom]);

  useEffect(() => {
    const simulation = simulationRef.current;
    const layoutNodes = nodesRef.current;
    if (!simulation || !layoutNodes.length) {
      return;
    }
    for (const node of layoutNodes) {
      node.radius = radiusById.get(node.id) ?? NEUTRAL_NODE_RADIUS;
    }
    simulation.force(
      "collide",
      forceCollide<SimNode>().radius((node) => node.radius + 6),
    );
    simulation.alpha(0.15).restart();
    syncGraphDom(layoutNodes);
  }, [radiusById, syncGraphDom]);

  useEffect(() => {
    let active = true;
    let raf = 0;
    const loop = () => {
      if (!active) {
        return;
      }
      const target = computeTargetViewBox(
        positionsRef.current,
        zoomScaleRef.current,
        manualPanRef.current.x,
        manualPanRef.current.y,
      );
      const current = viewBoxRef.current;
      const viewBox = {
        x: current.x + (target.x - current.x) * CAMERA_LERP,
        y: current.y + (target.y - current.y) * CAMERA_LERP,
        w: current.w + (target.w - current.w) * CAMERA_LERP,
        h: current.h + (target.h - current.h) * CAMERA_LERP,
      };
      viewBoxRef.current = viewBox;
      if (svgRef.current) {
        svgRef.current.setAttribute(
          "viewBox",
          `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`,
        );
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => {
      active = false;
      cancelAnimationFrame(raf);
    };
  }, []);

  const setZoom = useCallback((nextScale: number) => {
    zoomScaleRef.current = clamp(nextScale, ZOOM_MIN, ZOOM_MAX);
    setZoomLabel(Math.round(zoomScaleRef.current * 100));
  }, []);

  const resetCamera = useCallback(() => {
    manualPanRef.current = { x: 0, y: 0 };
    zoomScaleRef.current = 1;
    setZoomLabel(100);
  }, []);

  const clientToWorld = useCallback((clientX: number, clientY: number): { x: number; y: number } | null => {
    const svg = svgRef.current;
    if (!svg) {
      return null;
    }
    const rect = svg.getBoundingClientRect();
    const vb = viewBoxRef.current;
    const nx = (clientX - rect.left) / rect.width;
    const ny = (clientY - rect.top) / rect.height;
    return { x: vb.x + nx * vb.w, y: vb.y + ny * vb.h };
  }, []);

  function onWheel(event: React.WheelEvent<SVGSVGElement>) {
    event.preventDefault();
    const svg = svgRef.current;
    if (!svg) {
      return;
    }
    const screenWidth = svg.clientWidth || WIDTH;
    const screenHeight = svg.clientHeight || HEIGHT;
    const vb = viewBoxRef.current;
    manualPanRef.current = {
      x: manualPanRef.current.x + event.deltaX * (vb.w / screenWidth),
      y: manualPanRef.current.y + event.deltaY * (vb.h / screenHeight),
    };
  }

  function onBackgroundMouseDown(event: React.MouseEvent<SVGSVGElement>) {
    if (event.target !== event.currentTarget) {
      return;
    }
    setPanning({
      startX: event.clientX,
      startY: event.clientY,
      panX: manualPanRef.current.x,
      panY: manualPanRef.current.y,
    });
  }

  function onMouseMove(event: React.MouseEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (panning && svg) {
      const vb = viewBoxRef.current;
      const screenWidth = svg.clientWidth || WIDTH;
      const screenHeight = svg.clientHeight || HEIGHT;
      manualPanRef.current = {
        x: panning.panX - (event.clientX - panning.startX) * (vb.w / screenWidth),
        y: panning.panY - (event.clientY - panning.startY) * (vb.h / screenHeight),
      };
      return;
    }
    if (draggingId) {
      const point = clientToWorld(event.clientX, event.clientY);
      if (!point) {
        return;
      }
      const node = nodesRef.current.find((item) => item.id === draggingId);
      if (node) {
        node.fx = point.x;
        node.fy = point.y;
        simulationRef.current?.alpha(0.3).restart();
      }
    }
  }

  function onMouseUp() {
    if (draggingId) {
      const node = nodesRef.current.find((item) => item.id === draggingId);
      if (node) {
        node.fx = null;
        node.fy = null;
        simulationRef.current?.alphaTarget(0.02).alpha(0.3).restart();
      }
    }
    setPanning(null);
    setDraggingId(null);
  }

  return (
    <div style={{ position: "relative" }}>
      <div style={{ border: "1px solid var(--mantine-color-gray-3)", background: "#fafafa", overflow: "auto" }}>
        <svg
          ref={svgRef}
          width="100%"
          viewBox={INITIAL_VIEWBOX}
          style={{ minWidth: 900, height: 860, display: "block", cursor: panning ? "grabbing" : "default" }}
          onClick={() => onSelectModule(null)}
          onWheel={onWheel}
          onMouseDown={onBackgroundMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
        >
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="8"
              markerHeight="8"
              markerUnits="userSpaceOnUse"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280" />
            </marker>
          </defs>
          <rect
            x={0}
            y={0}
            width={WIDTH}
            height={HEIGHT}
            fill="transparent"
            onMouseDown={(event) => {
              event.stopPropagation();
              setPanning({
                startX: event.clientX,
                startY: event.clientY,
                panX: manualPanRef.current.x,
                panY: manualPanRef.current.y,
              });
            }}
          />
          {simLinks.map((link) => {
            const sourceId = linkEndpointId(link.source);
            const targetId = linkEndpointId(link.target);
            const key = `${sourceId}-${targetId}-${link.offset}`;
            const thickness = edgeStrokeWidth(link.edge.breakdown.total);
            return (
              <path
                key={key}
                ref={(element) => {
                  if (element) {
                    linkPathRefs.current.set(key, element);
                  } else {
                    linkPathRefs.current.delete(key);
                  }
                }}
                d=""
                fill="none"
                stroke="#6b7280"
                strokeWidth={thickness}
                markerEnd="url(#arrow)"
              >
                <title>{buildEdgeTooltip(link.edge)}</title>
              </path>
            );
          })}
          {simNodes.map((simNode) => {
            const visible = lineCategoryTotal(simNode.node.line_categories, lineCategories);
            const complexityRatio = brightnessCriteria.size ? (brightnessById.get(simNode.id) ?? 0) : 0;
            const fill = colorForComplexityRatio(complexityRatio);
            const stroke = selectedModule === simNode.id
              ? "#dc2626"
              : strokeForComplexityRatio(complexityRatio);
            const valueColor = textColorForComplexityRatio(complexityRatio);
            const showVisible = lineCategories.size > 0;
            const nodeRadius = simNode.radius;
            const valueFontSize = Math.max(10, Math.min(16, nodeRadius * 0.33));
            return (
              <g
                key={simNode.id}
                ref={(element) => {
                  if (element) {
                    nodeGroupRefs.current.set(simNode.id, element);
                    const layoutNode = nodesRef.current.find((item) => item.id === simNode.id);
                    if (layoutNode?.x != null && layoutNode?.y != null) {
                      element.setAttribute("transform", `translate(${layoutNode.x}, ${layoutNode.y})`);
                    }
                  } else {
                    nodeGroupRefs.current.delete(simNode.id);
                  }
                }}
                style={{ cursor: "grab" }}
                onMouseDown={(event) => {
                  event.stopPropagation();
                  setDraggingId(simNode.id);
                }}
                onClick={(event) => {
                  event.stopPropagation();
                  onSelectModule(selectedModule === simNode.id ? null : simNode.id);
                }}
              >
                <title>{buildNodeTooltip(simNode.node, visible)}</title>
                <circle
                  r={nodeRadius}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={selectedModule === simNode.id ? 3 : 1.5}
                />
                {showVisible ? (
                  <text textAnchor="middle" dy={4} fontSize={valueFontSize} fill={valueColor}>
                    {formatCodeLines(visible)}
                  </text>
                ) : null}
                <text textAnchor="middle" dy={-(nodeRadius + 10)} fontSize={11} fill="#111827">
                  {simNode.id}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      {loading ? (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(255,255,255,0.72)",
          }}
        >
          <Text size="sm" c="dimmed">
            Loading graph…
          </Text>
        </div>
      ) : null}
      <Group mt="xs">
        <Button size="xs" variant="light" onClick={() => setZoom(zoomScaleRef.current * ZOOM_STEP)}>
          Zoom in
        </Button>
        <Button size="xs" variant="light" onClick={() => setZoom(zoomScaleRef.current / ZOOM_STEP)}>
          Zoom out
        </Button>
        <Button size="xs" variant="light" onClick={resetCamera}>
          Fit
        </Button>
        <Text size="sm" c="dimmed">
          Zoom {zoomLabel}% · wheel pans · camera follows graph
        </Text>
      </Group>
    </div>
  );
}
