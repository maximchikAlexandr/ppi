/**
 * Generic graph layout adapter.
 *
 * Wraps d3-force behaviour so generic code only reads `EntityRef`
 * ids and never branches on entity-name special cases.
 */
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  type Simulation,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from "d3-force";

import type { EntityGraphEdge, EntityGraphModel, EntityGraphNode } from "../../../domain/graph";

type SimNode = SimulationNodeDatum & {
  id: string;
  entity: EntityGraphNode["entity"];
  radius: number;
};

type SimLink = SimulationLinkDatum<SimNode> & {
  id: string;
  edge: EntityGraphEdge;
};

export function buildGraphLayout(model: EntityGraphModel): {
  nodes: SimNode[];
  links: SimLink[];
  run: (iterations: number) => Simulation<SimNode, SimLink>;
} {
  const nodes: SimNode[] = model.nodes.map((n) => ({
    id: n.entity.id,
    entity: n.entity,
    radius: 30,
  }));
  const links: SimLink[] = model.edges.map((e) => ({
    id: e.id,
    source: e.source.id,
    target: e.target.id,
    edge: e,
  }));
  const run = (iterations: number) => {
    const sim = forceSimulation<SimNode, SimLink>(nodes)
      .force("charge", forceManyBody().strength(-120))
      .force("center", forceCenter(0, 0))
      .force("collide", forceCollide<SimNode>((d) => d.radius + 4))
      .force("link", forceLink<SimNode, SimLink>(links).id((d) => d.id).distance(80));
    sim.stop();
    sim.tick(iterations);
    return sim;
  };
  return { nodes, links, run };
}
