/**
 * useEntityGraphSimulation: imperative d3-force shell.
 *
 * d3 force simulation is an imperative API; the hook owns the
 * Simulation instance, its alpha, and the start/stop lifecycle. The
 * pure layout is still `buildGraphLayout` (entityGraphLayout.ts);
 * this hook is just the lifecycle driver.
 */
import { useEffect, useRef, useState } from "react";

import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  type Simulation,
} from "d3-force";

import type { EntityGraphEdge, EntityGraphModel, EntityGraphNode } from "../../../domain/graph";

type SimNode = {
  id: string;
  entity: EntityGraphNode["entity"];
  radius: number;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
};

type SimLink = {
  id: string;
  edge: EntityGraphEdge;
  source: SimNode | string;
  target: SimNode | string;
};

type ForceState = {
  charge: number;
  linkDistance: number;
  centerStrength: number;
  collidePadding: number;
};

export type UseEntityGraphSimulationOptions = {
  readonly model: EntityGraphModel;
  readonly forces?: Partial<ForceState>;
};

export type UseEntityGraphSimulationResult = {
  readonly nodes: readonly SimNode[];
  readonly links: readonly SimLink[];
  readonly restart: () => void;
  readonly stop: () => void;
  readonly tick: (iterations: number) => void;
};

const DEFAULTS: ForceState = {
  charge: -120,
  linkDistance: 80,
  centerStrength: 0.1,
  collidePadding: 4,
};

export function useEntityGraphSimulation({
  model,
  forces,
}: UseEntityGraphSimulationOptions): UseEntityGraphSimulationResult {
  const [state, setState] = useState<{ nodes: SimNode[]; links: SimLink[] }>(() => init(model));
  const simRef = useRef<Simulation<SimNode, SimLink> | null>(null);
  const forcesMerged: ForceState = { ...DEFAULTS, ...(forces ?? {}) };

  useEffect(() => {
    const { nodes, links } = init(model);
    setState({ nodes, links });
  }, [model]);

  useEffect(() => {
    const sim = forceSimulation<SimNode, SimLink>(state.nodes)
      .force("charge", forceManyBody<SimNode>().strength(forcesMerged.charge))
      .force("center", forceCenter(0, 0).strength(forcesMerged.centerStrength))
      .force("collide", forceCollide<SimNode>((d) => d.radius + forcesMerged.collidePadding))
      .force(
        "link",
        forceLink<SimNode, SimLink>(state.links)
          .id((d) => d.id)
          .distance(forcesMerged.linkDistance),
      )
      .alpha(0.3)
      .alphaMin(0.001)
      .alphaDecay(0.02)
      .on("tick", () => {
        setState((s) => ({ nodes: [...s.nodes], links: s.links }));
      });
    simRef.current = sim;
    return () => {
      sim.stop();
      simRef.current = null;
    };
  }, [state.nodes, state.links, forcesMerged]);

  return {
    nodes: state.nodes,
    links: state.links,
    restart: () => simRef.current?.alpha(0.8).restart(),
    stop: () => simRef.current?.stop(),
    tick: (n) => {
      simRef.current?.stop();
      for (let i = 0; i < n; i++) simRef.current?.tick();
      setState((s) => ({ nodes: [...s.nodes], links: s.links }));
    },
  };
}

function init(model: EntityGraphModel): { nodes: SimNode[]; links: SimLink[] } {
  const nodes: SimNode[] = model.nodes.map((n) => ({
    id: n.entity.id,
    entity: n.entity,
    radius: 30,
  }));
  const links: SimLink[] = model.edges.map((e) => ({
    id: e.id,
    edge: e,
    source: e.source.id,
    target: e.target.id,
  }));
  return { nodes, links };
}
