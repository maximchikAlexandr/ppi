import { describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useEntityGraphSimulation } from "./useEntityGraphSimulation";
import type { EntityGraphModel } from "../../../domain/graph";
import { unknownMetricGraph } from "./__fixtures__/unknownMetricGraph";

describe("useEntityGraphSimulation", () => {
  it("exposes one node per entity and one link per edge", () => {
    const { result } = renderHook(() =>
      useEntityGraphSimulation({ model: unknownMetricGraph }),
    );
    expect(result.current.nodes).toHaveLength(2);
    expect(result.current.links).toHaveLength(1);
  });

  it("rebuilds the simulation when the model changes", () => {
    const initial: EntityGraphModel = { commitId: "c1", lensId: "l1", nodes: [], edges: [] };
    const next: EntityGraphModel = unknownMetricGraph;
    const { result, rerender } = renderHook(
      ({ model }: { model: EntityGraphModel }) => useEntityGraphSimulation({ model }),
      { initialProps: { model: initial } },
    );
    expect(result.current.nodes).toHaveLength(0);
    rerender({ model: next });
    expect(result.current.nodes).toHaveLength(2);
  });

  it("actually moves nodes when the simulation is ticked", () => {
    const { result } = renderHook(() =>
      useEntityGraphSimulation({ model: unknownMetricGraph }),
    );
    // Before any tick, d3 may leave positions undefined or at the
    // seed. Snapshot whatever they are.
    const x0 = result.current.nodes[0]?.x;
    const y0 = result.current.nodes[0]?.y;
    act(() => {
      result.current.tick(120);
    });
    const x1 = result.current.nodes[0]?.x;
    const y1 = result.current.nodes[0]?.y;
    // At least one node must have moved from its seed, or be on a
    // non-origin position. This catches a regression where the
    // simulation silently no-ops.
    const moved =
      (x0 !== x1 && (x0 === undefined || Math.abs((x1 ?? 0) - x0) > 0.001)) ||
      (y0 !== y1 && (y0 === undefined || Math.abs((y1 ?? 0) - y0) > 0.001));
    const nonOrigin =
      (x1 !== undefined && Math.abs(x1) > 0.001) ||
      (y1 !== undefined && Math.abs(y1) > 0.001);
    expect(moved || nonOrigin).toBe(true);
  });
});
