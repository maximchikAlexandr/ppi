/**
 * EntityGraph: renders an EntityGraphModel. Reads entity ids from
 * EntityRef; does not branch on legacy Python/Odoo identifiers.
 *
 * Layout is the imperative d3-force simulation; pure node / edge
 * display calculation lives in entityGraphLayout.ts. This component
 * is the shell that wires them together.
 */
import { useMemo } from "react";
import { Group, Text } from "@mantine/core";

import type { EntityGraphModel } from "../../../domain/graph";
import { useUiConfig } from "../../../registry/UiConfigProvider";
import { buildNodeTooltip, buildEdgeTooltip } from "./entityGraphTooltips";
import { useEntityGraphSimulation } from "./useEntityGraphSimulation";
type Props = {
  model: EntityGraphModel;
  onSelectNode?: (entityId: string) => void;
};

export function EntityGraph({ model, onSelectNode }: Props) {
  const { registry } = useUiConfig();
  const sim = useEntityGraphSimulation({ model });
  // Kick the simulation once per model change so the layout settles
  // before the first paint. The shell hook owns restart/stop.
  useMemo(() => {
    sim.tick(60);
    // intentionally only depend on model identity, not the sim API
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model]);

  const positions = useMemo(() => {
    const m = new Map<string, { x: number; y: number }>();
    for (const n of sim.nodes) {
      m.set(n.id, { x: n.x ?? 0, y: n.y ?? 0 });
    }
    return m;
  }, [sim.nodes]);

  const lookupTarget = (link: (typeof sim.links)[number]) => {
    const s = typeof link.source === "string" ? sim.nodes.find((n) => n.id === link.source) : link.source;
    const t = typeof link.target === "string" ? sim.nodes.find((n) => n.id === link.target) : link.target;
    return { s, t };
  };

  return (
    <svg
      role="img"
      aria-label="Generic entity graph"
      data-testid="entity-graph"
      width="100%"
      height={400}
    >
      <Group>
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
          return (
            <g
              key={node.id}
              data-testid="graph-node"
              data-tip={tip}
              transform={`translate(${p.x},${p.y})`}
              onClick={() => onSelectNode?.(node.id)}
              style={{ cursor: "pointer" }}
            >
              <circle r={node.radius} fill="teal" />
              <Text component="text" x={0} y={4} textAnchor="middle" fill="white">
                {node.entity.label}
              </Text>
            </g>
          );
        })}
      </Group>
    </svg>
  );
}
