import { describe, expect, it } from "vitest";
import { renderHook } from "@testing-library/react";

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
});
