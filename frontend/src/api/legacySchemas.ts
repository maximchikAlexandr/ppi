import { z } from "zod";

export const CommitRowSchema = z.object({
  commit_hash: z.string(),
  commit_order: z.number(),
  authored_at: z.string().nullable().optional(),
  summary: z.string().nullable().optional(),
});

export const GraphNodeSchema = z.object({
  module_name: z.string(),
  total_lines: z.number(),
  metrics: z.record(z.string(), z.number()),
  line_counts: z.record(z.string(), z.number()),
});

export const GraphEdgeSchema = z.object({
  source: z.string(),
  target: z.string(),
  score: z.number(),
  kinds: z.record(z.string(), z.number()).default({}),
  kind_occurrence_count: z.number().default(0),
  breakdown: z.record(z.string(), z.number()).nullable().optional(),
  commit_hash: z.string().default(""),
});

export const GraphResponseSchema = z.object({
  commit_hash: z.string(),
  nodes: z.array(GraphNodeSchema),
  edges: z.array(GraphEdgeSchema),
});

export const HotspotItemSchema = z.object({
  name: z.string(),
  current: z.number(),
  first: z.number().nullable().optional(),
  growth: z.number().nullable().optional(),
});

export const HotspotsResponseSchema = z.object({
  by: z.string(),
  items: z.array(HotspotItemSchema),
});

export const TimeseriesPointSchema = z.object({
  commit_order: z.number(),
  commit_hash: z.string(),
  value: z.number().nullable().optional(),
});

export const TimeseriesSeriesSchema = z.object({
  name: z.string(),
  points: z.array(TimeseriesPointSchema),
});

export const TimeseriesResponseSchema = z.object({
  level: z.string(),
  metric_id: z.string(),
  agg: z.string(),
  series: z.array(TimeseriesSeriesSchema),
});

export const UiOptionSchema = z.object({
  id: z.string(),
  label: z.string(),
  default_enabled: z.boolean().default(false),
});

export const UiMetricOptionSchema = z.object({
  id: z.string(),
  label: z.string(),
  unit: z.string().default(""),
  format: z.string().default(""),
  default_enabled: z.boolean().default(false),
  supported_levels: z.array(z.enum(["module", "file"])).default([]),
});

export const UiColumnDefinitionSchema = z.object({
  key: z.string(),
  label: z.string(),
  type: z.string().default("string"),
  metric_id: z.string().nullable().optional(),
  width: z.number().nullable().optional(),
});

export const UiTableDefinitionSchema = z.object({
  key: z.string(),
  label: z.string(),
  columns: z.array(UiColumnDefinitionSchema),
});

export const UiGraphConfigSchema = z.object({
  edge_types: z.array(UiOptionSchema),
  line_categories: z.array(UiOptionSchema),
  brightness_metrics: z.array(UiMetricOptionSchema),
  node_size_metrics: z.array(UiMetricOptionSchema),
  link_thickness_metrics: z.array(UiMetricOptionSchema),
});

export const UiConfigResponseSchema = z.object({
  dashboard_metrics: z.array(UiMetricOptionSchema),
  aggregations: z.array(UiOptionSchema),
  tables: z.array(UiTableDefinitionSchema),
  graph: UiGraphConfigSchema,
});

export const GenericTableRowSchema = z.object({
  id: z.string().default(""),
  cells: z.record(z.string(), z.unknown()),
  actions: z.record(z.string(), z.boolean()).optional(),
});

export const GenericTableResponseSchema = z.object({
  commit_hash: z.string(),
  rows: z.array(GenericTableRowSchema),
});

export const RelationRowSchema = z.object({
  source_id: z.string(),
  source_label: z.string(),
  target_id: z.string(),
  target_label: z.string(),
  relation_type_id: z.string(),
  relation_type_label: z.string(),
  strength_metric_id: z.string().default(""),
  strength_metric_label: z.string().default(""),
  strength_value: z.number().default(0),
});

export const RelationsResponseSchema = z.object({
  commit_hash: z.string(),
  relations: z.array(RelationRowSchema),
});

export const ProjectInfoResponseSchema = z.object({
  project_id: z.string().nullable().optional(),
  branch: z.string().nullable().optional(),
  commit_count: z.number().default(0),
  schema_version: z.number(),
  store_present: z.boolean(),
});

export const ResponseEnvelopeSchema = z.discriminatedUnion("status", [
  z.object({
    kind: z.literal("response"),
    status: z.literal("ok"),
    id: z.number(),
    result: z.unknown(),
  }),
  z.object({
    kind: z.literal("response"),
    status: z.literal("error"),
    id: z.number(),
    error: z.object({
      code: z.string(),
      message: z.string(),
      details: z.unknown().optional(),
    }),
  }),
]);

export const RequestEnvelopeSchema = z.object({
  method: z.string(),
  params: z.record(z.string(), z.unknown()).default({}),
});
