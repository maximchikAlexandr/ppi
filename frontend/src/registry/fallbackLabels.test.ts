import { describe, expect, it } from "vitest";

import { fallbackLabel } from "./fallbackLabels";

describe("fallbackLabel", () => {
  it.each([
    ["odoo.module", "Odoo Module"],
    ["python_file_count", "Python File Count"],
    ["kebab-case-id", "Kebab Case Id"],
    ["path/with/slashes", "Path With Slashes"],
    ["", "—"],
    ["   ", "—"],
    ["   .  _  -  /   ", "—"],
    [null, "—"],
    [undefined, "—"],
  ])("converts %p to %p", (input, expected) => {
    expect(fallbackLabel(input as string)).toBe(expected);
  });
});
