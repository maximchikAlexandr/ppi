/// <reference types="vitest" />
import React from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";

import { GenericDataTable } from "./GenericDataTable";
import { UiConfigProvider } from "../../../registry/UiConfigProvider";
import { unknownUiConfig } from "../../../registry/__fixtures__/unknownUiConfig";
import { genericTable } from "./__fixtures__/genericTable";
import { unknownColumnsTable } from "./__fixtures__/unknownColumnsTable";

function wrap(node: React.ReactNode) {
  return (
    <MantineProvider>
      <UiConfigProvider loader={async () => unknownUiConfig}>
        {node}
      </UiConfigProvider>
    </MantineProvider>
  );
}

describe("GenericDataTable", () => {
  it("renders unknown columns and row actions", () => {
    render(wrap(<GenericDataTable projection={genericTable} />));
    expect(screen.getByText("Weird Column")).toBeTruthy();
    expect(screen.getByTestId("generic-row")).toBeTruthy();
  });

  it("triggers drilldown action handler", () => {
    const onAction = vi.fn();
    render(wrap(<GenericDataTable projection={genericTable} onAction={onAction} />));
    fireEvent.click(screen.getByText("Open"));
    expect(onAction).toHaveBeenCalled();
  });

  it("renders columns whose metricIds are unknown to the registry", () => {
    const { container } = render(wrap(<GenericDataTable projection={unknownColumnsTable} />));
    expect(screen.getByText("Fremium Score")).toBeTruthy();
    expect(screen.getByText("Fremium %")).toBeTruthy();
    expect(screen.getByText("Updated at")).toBeTruthy();
    expect(container.querySelectorAll('[data-testid="generic-row"]')).toHaveLength(2);
    expect(container.innerHTML).not.toContain("module_name");
  });
});
