import { describe, expect, it } from "vitest";

describe("adapter boundary", () => {
  it("adapters do not leak raw generated DTO wrappers", async () => {
    const fs = await import("node:fs/promises");
    const path = await import("node:path");
    const root = path.join(process.cwd(), "src/api/adapters");
    const entries = await fs.readdir(root);
    for (const entry of entries) {
      if (!entry.endsWith(".ts") || entry.endsWith(".test.ts")) continue;
      const content = await fs.readFile(path.join(root, entry), "utf8");
      // Generated DTOs have branded wrapper types like GeneratedSchemas; generic
      // components should not import them. The adapters themselves are allowed
      // because they bridge to domain types, but they must not export
      // `paths` or `components` from generated.
      expect(content).not.toMatch(/export\s+\{[^}]*paths[^}]*\}/);
      expect(content).not.toMatch(/export\s+\{[^}]*components[^}]*\}/);
    }
  });
});
