/// <reference types="vitest" />
import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";

import { EntityGraph } from "./EntityGraph";
import { UiConfigProvider } from "../../../registry/UiConfigProvider";
import { unknownUiConfig } from "../../../registry/__fixtures__/unknownUiConfig";
import { nonModuleGraph } from "./__fixtures__/nonModuleGraph";
import { unknownMetricGraph } from "./__fixtures__/unknownMetricGraph";

function wrap(node: React.ReactNode) {
  return (
    <MantineProvider>
      <UiConfigProvider loader={async () => unknownUiConfig}>
        {node}
      </UiConfigProvider>
    </MantineProvider>
  );
}

describe("EntityGraph", () => {
  it("renders nodes and edges without module_name", () => {
    const { container } = render(wrap(<EntityGraph model={nonModuleGraph} />));
    expect(container.innerHTML).not.toContain("module_name");
    expect(screen.getAllByTestId("graph-node")).toHaveLength(2);
    expect(screen.getAllByTestId("graph-edge")).toHaveLength(1);
  });

  it("does not render fixed breakdown fields", () => {
    const { container } = render(wrap(<EntityGraph model={nonModuleGraph} />));
    expect(container.innerHTML).not.toMatch(/breakdown/);
  });

  it("renders a graph whose metric ids are not in the registry", () => {
    const { container } = render(wrap(<EntityGraph model={unknownMetricGraph} />));
    // Two nodes + one edge, no crash, no domain tokens leaked.
    expect(screen.getAllByTestId("graph-node")).toHaveLength(2);
    expect(screen.getAllByTestId("graph-edge")).toHaveLength(1);
    expect(container.innerHTML).not.toContain("module_name");
    expect(container.innerHTML).not.toContain("breakdown");
  });
});
