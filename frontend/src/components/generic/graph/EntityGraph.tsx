/**
 * EntityGraph: renders an EntityGraphModel. Reads entity ids from
 * EntityRef; does not branch on legacy Python/Odoo identifiers.
 */
import { useMemo } from "react";
import { Group, Text } from "@mantine/core";

import type { EntityGraphModel } from "../../../domain/graph";
import { useUiConfig } from "../../../registry/UiConfigProvider";
import { buildGraphLayout } from "./entityGraphLayout";
import { buildNodeTooltip, buildEdgeTooltip } from "./entityGraphTooltips";

type Props = {
  model: EntityGraphModel;
  onSelectNode?: (entityId: string) => void;
};

export function EntityGraph({ model, onSelectNode }: Props) {
  const { registry } = useUiConfig();
  const layout = useMemo(() => buildGraphLayout(model), [model]);
  const positions = useMemo(() => {
    layout.run(120);
    return new Map(layout.nodes.map((n) => [n.id, n]));
  }, [layout]);

  return (
    <svg
      role="img"
      aria-label="Generic entity graph"
      data-testid="entity-graph"
      width="100%"
      height={400}
    >
      <Group>
        {model.edges.map((edge) => {
          const s = positions.get(edge.source.id);
          const t = positions.get(edge.target.id);
          if (!s || !t) return null;
          const x1 = (s.x ?? 0);
          const y1 = (s.y ?? 0);
          const x2 = (t.x ?? 0);
          const y2 = (t.y ?? 0);
          const tip = registry ? buildEdgeTooltip(edge, registry) : "";
          return (
            <line
              key={edge.id}
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
        {model.nodes.map((node) => {
          const p = positions.get(node.entity.id);
          if (!p) return null;
          const tip = registry ? buildNodeTooltip(node, registry) : node.entity.label;
          return (
            <g
              key={node.entity.id}
              data-testid="graph-node"
              data-tip={tip}
              transform={`translate(${p.x ?? 0},${p.y ?? 0})`}
              onClick={() => onSelectNode?.(node.entity.id)}
              style={{ cursor: "pointer" }}
            >
              <circle r={p.radius} fill="teal" />
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
