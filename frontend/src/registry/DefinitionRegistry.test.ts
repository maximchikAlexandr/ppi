import { describe, expect, it } from "vitest";

import { DefinitionRegistry } from "./DefinitionRegistry";
import { unknownUiConfig } from "./__fixtures__/unknownUiConfig";

describe("DefinitionRegistry", () => {
  it("returns definitions for known ids", () => {
    const reg = new DefinitionRegistry(unknownUiConfig);
    expect(reg.getMetric("test.unknown_metric")?.label).toBe("Unknown Metric");
    expect(reg.getEntityKind("test.unknown_kind")?.label).toBe("Unknown Kind");
    expect(reg.getRelationType("test.unknown_relation")?.label).toBe("Unknown Relation");
    expect(reg.getTable("test.unknown_table")?.label).toBe("Unknown Table");
    expect(reg.getGraphLens("test.unknown_lens")?.label).toBe("Unknown Lens");
  });

  it("falls back to deterministic labels for unknown ids", () => {
    const reg = new DefinitionRegistry(unknownUiConfig);
    expect(reg.metricLabel("not_in_registry")).toBe("Not In Registry");
    expect(reg.relationTypeLabel("weird.id.with-dashes/slashes")).toBe(
      "Weird Id With Dashes Slashes",
    );
    expect(reg.tableLabel("missing_table")).toBe("Missing Table");
  });
});
