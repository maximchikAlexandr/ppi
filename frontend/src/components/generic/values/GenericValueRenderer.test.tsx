/// <reference types="vitest" />
import React from "react";
import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";

import { GenericValueRenderer } from "./GenericValueRenderer";
import { UiConfigProvider } from "../../../registry/UiConfigProvider";
import { unknownUiConfig } from "../../../registry/__fixtures__/unknownUiConfig";

afterEach(() => cleanup());

function wrap(node: React.ReactNode) {
  return (
    <UiConfigProvider loader={async () => unknownUiConfig}>{node}</UiConfigProvider>
  );
}

describe("GenericValueRenderer", () => {
  it("renders null as dash", () => {
    const { getByTestId } = render(wrap(<GenericValueRenderer value={null} />));
    expect(getByTestId("generic-value-null")).toBeTruthy();
  });

  it("renders booleans with stable labels", () => {
    const { getByTestId } = render(wrap(<GenericValueRenderer value={true} />));
    expect(getByTestId("boolean-true").textContent).toBe("yes");
  });

  it("escapes string values", () => {
    const { getByTestId } = render(
      wrap(<GenericValueRenderer value={"<script>alert(1)</script>"} valueType="string" />),
    );
    expect(getByTestId("generic-value-string").innerHTML).not.toContain("<script>");
  });

  it("falls back to escaped string for unknown value types", () => {
    const { getByTestId } = render(
      wrap(<GenericValueRenderer value={"plain_text"} valueType={"weird" as never} />),
    );
    expect(getByTestId("generic-value-string").textContent).toBe("plain_text");
  });
});
