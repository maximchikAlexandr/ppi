/**
 * useEntityGraphSimulation: imperative d3-force shell.
 *
 * d3 force simulation is an imperative API; the hook owns the
 * Simulation instance, its alpha, and the start/stop lifecycle. The
 * pure layout is still `buildGraphLayout` (entityGraphLayout.ts);
 * this hook is just the lifecycle driver.
 */
import { useEffect, useMemo, useRef, useState } from "react";

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
  readonly dragStart: (nodeId: string, x: number, y: number) => void;
  readonly dragMove: (nodeId: string, x: number, y: number) => void;
  readonly dragEnd: (nodeId: string) => void;
};

const DEFAULTS: ForceState = {
  charge: -45,
  linkDistance: 64,
  centerStrength: 0.18,
  collidePadding: 4,
};

export function useEntityGraphSimulation({
  model,
  forces,
}: UseEntityGraphSimulationOptions): UseEntityGraphSimulationResult {
  const [state, setState] = useState<{ nodes: SimNode[]; links: SimLink[] }>(() => init(model));
  const simRef = useRef<Simulation<SimNode, SimLink> | null>(null);
  const forcesMerged: ForceState = useMemo(
    () => ({ ...DEFAULTS, ...(forces ?? {}) }),
    [forces],
  );

  useEffect(() => {
    const next = init(model);
    setState(next);
    const sim = forceSimulation<SimNode, SimLink>(next.nodes)
      .force("charge", forceManyBody<SimNode>().strength(forcesMerged.charge))
      .force("center", forceCenter(0, 0).strength(forcesMerged.centerStrength))
      .force("collide", forceCollide<SimNode>((d) => d.radius + forcesMerged.collidePadding))
      .force(
        "link", forceLink<SimNode, SimLink>(next.links)
          .id((d) => d.id)
          .distance((link) => {
            const w = link.edge.metrics[0]?.value;
            const weight = typeof w === "number" ? w : 0;
            return Math.max(30, forcesMerged.linkDistance - weight * 0.3);
          })
          .strength((link) => {
            const w = link.edge.metrics[0]?.value;
            const weight = typeof w === "number" ? Math.max(0, w) : 0;
            return 0.1 + weight * 0.02;
          }),
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
  }, [
    model,
    forcesMerged.charge,
    forcesMerged.centerStrength,
    forcesMerged.collidePadding,
    forcesMerged.linkDistance,
  ]);

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
    dragStart: (nodeId, x, y) => {
      const node = state.nodes.find((n) => n.id === nodeId);
      if (!node) return;
      node.fx = x;
      node.fy = y;
      simRef.current?.alphaTarget(0.25).restart();
      setState((s) => ({ nodes: [...s.nodes], links: s.links }));
    },
    dragMove: (nodeId, x, y) => {
      const node = state.nodes.find((n) => n.id === nodeId);
      if (!node) return;
      node.fx = x;
      node.fy = y;
      setState((s) => ({ nodes: [...s.nodes], links: s.links }));
    },
    dragEnd: (nodeId) => {
      const node = state.nodes.find((n) => n.id === nodeId);
      if (!node) return;
      node.fx = null;
      node.fy = null;
      simRef.current?.alphaTarget(0).restart();
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
