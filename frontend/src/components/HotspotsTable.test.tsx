/// <reference types="vitest" />
import { MantineProvider } from "@mantine/core";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HotspotsTable } from "./HotspotsTable";

const item = {
  entity: { id: "one", kind: "test.entity", label: "Entity one" },
  current: 4,
  first: null,
  growth: null,
};

describe("HotspotsTable", () => {
  it("does not present current-value rows as a growth ranking", () => {
    render(
      <MantineProvider>
        <HotspotsTable title="Growth" items={[item]} showGrowth />
      </MantineProvider>,
    );

    expect(screen.getByText("Данных пока нет.")).toBeTruthy();
    expect(screen.queryByText("Entity one")).toBeNull();
  });
});
