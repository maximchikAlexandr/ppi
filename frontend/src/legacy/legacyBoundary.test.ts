/**
 * Legacy boundary regression tests. The Python script
 * `scripts/check_frontend_boundaries.py` is the source of truth; this
 * TS test re-implements the *path-only* logic so Vitest can exercise
 * it without spawning a Python process.
 */
import { describe, expect, it } from "vitest";

const GENERIC_PREFIXES = [
  "frontend/src/api",
  "frontend/src/domain",
  "frontend/src/registry",
  "frontend/src/components/generic",
  "frontend/src/pages",
  "frontend/src/visualization",
] as const;

const EXEMPT_PATHS = [
  "frontend/src/legacy",
  "frontend/src/api/adapters",
  "frontend/src/api/publicApi.ts",
  "frontend/src/api/internalApi.ts",
  "frontend/src/api/http.ts",
  "frontend/src/api/generated/",
  "frontend/src/api/__fixtures__/analysisResponses.ts",
  "frontend/src/pages/SnapshotPage.tsx",
] as const;

const FORBIDDEN_TOKENS = [
  "module_name",
  "python_file_count",
  "cyclomatic",
  "cognitive",
  "jones",
  "manifest_depends",
  "model_reuse",
  "field_property",
  "extension_or_method",
  "python_lines",
  "xml_lines",
  "score_in",
  "score_out",
] as const;

function isExempt(rel: string): boolean {
  return EXEMPT_PATHS.some((p) => rel.startsWith(p));
}

function isGeneric(rel: string): boolean {
  if (rel.endsWith(".test.ts") || rel.endsWith(".test.tsx") || rel.endsWith("_test.py")) {
    return false;
  }
  if (isExempt(rel)) return false;
  return GENERIC_PREFIXES.some((p) => rel.startsWith(p));
}

function scanTs(rel: string, content: string): { line: number; token: string }[] {
  const violations: { line: number; token: string }[] = [];
  if (!isGeneric(rel)) return violations;
  for (let i = 0; i < content.split("\n").length; i++) {
    const line = content.split("\n")[i] ?? "";
    if (/from\s+['"][^'"]*generated/.test(line) || /from\s+['"][^'"]*\/generated\//.test(line)) {
      violations.push({ line: i + 1, token: "generated DTO import" });
    }
    if (/from\s+['"][^'"]*\/legacy\//.test(line)) {
      violations.push({ line: i + 1, token: "legacy import" });
    }
  }
  return violations;
}

describe("legacy boundary", () => {
  it("generic code may not import legacy modules", () => {
    const violations = scanTs(
      "frontend/src/domain/fake.ts",
      `import { legacyGraphToGenericGraph } from "../legacy/legacyGraphAdapter";\n`,
    );
    expect(violations.length).toBeGreaterThan(0);
  });

  it("legacy code may import legacy modules and DTOs", () => {
    const violations = scanTs(
      "frontend/src/legacy/legacyGraphAdapter.ts",
      `import { paths } from "../api/generated/schema";\nconst x = "module_name";\n`,
    );
    expect(violations).toEqual([]);
  });
});
