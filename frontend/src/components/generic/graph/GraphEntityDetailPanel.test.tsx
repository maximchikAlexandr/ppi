/// <reference types="vitest" />
import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";

import { GraphEntityDetailPanel } from "./GraphEntityDetailPanel";
import { UiConfigProvider } from "../../../registry/UiConfigProvider";
import { unknownUiConfig } from "../../../registry/__fixtures__/unknownUiConfig";

describe("GraphEntityDetailPanel", () => {
  it("renders registry-driven metrics for an arbitrary entity kind", async () => {
    render(
      <MantineProvider>
        <UiConfigProvider loader={async () => unknownUiConfig}>
          <GraphEntityDetailPanel
            node={{
              entity: { id: "entity-1", kind: "test.unknown_kind", label: "Entity one" },
              metrics: [
                { metricId: "test.unknown_metric", value: 12.5, aggregation: "mean" },
                { metricId: "test.unknown_metric", value: 20, aggregation: "max" },
              ],
              lineCounts: { "test.unknown_line": 42 },
            }}
            emptyLabel="Pick an entity"
            metricsLabel="Metrics"
            lineCountsLabel="Lines"
          />
        </UiConfigProvider>
      </MantineProvider>,
    );

    expect(await screen.findByText("Unknown Kind")).toBeTruthy();
    expect(screen.getByText("Unknown Metric")).toBeTruthy();
    expect(screen.getByText("Unknown Line")).toBeTruthy();
    expect(screen.getByText("Mean")).toBeTruthy();
    expect(screen.getByText("Max")).toBeTruthy();
    expect(screen.getAllByText("Unknown Metric")).toHaveLength(1);
    expect(document.body.innerHTML).not.toContain("module_name");
  });
});
