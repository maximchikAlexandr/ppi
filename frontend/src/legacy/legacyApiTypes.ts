// ─────────────────────────────────────────────────────────────────
// Forbidden domain identifiers for the GENERIC frontend.
//
// Generic components and pages must NOT reference these strings.
// They belong to legacy Python/Odoo-specific schemas and may only be
// used inside `frontend/src/legacy/**` and adapter tests.
//
// Forbidden tokens (any of these appearing in a generic file is a
// boundary violation):
//   module_name, python_file_count, cyclomatic, cognitive, jones,
//   manifest_depends, model_reuse, field_property, extension_or_method,
//   python_lines, xml_lines, score_in, score_out
//
// If a generic component needs one of these, route it through a
// backend definition (metric / relation type / entity kind) instead.
// ─────────────────────────────────────────────────────────────────

export type LegacyCommitRow = {
  commit_hash: string;
  commit_order: number;
  authored_at: string | null;
  summary: string | null;
};

export type LegacyGraphNode = {
  module_name: string;
  total_lines: number;
  metrics: Record<string, number>;
  line_counts: Record<string, number>;
};

export type LegacyGraphEdge = {
  source: string;
  target: string;
  score: number;
  kinds: Record<string, number>;
  breakdown: Record<string, number> | null;
  commit_hash: string;
};

export type LegacyUiConfig = unknown;
