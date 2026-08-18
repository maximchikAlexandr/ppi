import { Badge, Group, Paper, SimpleGrid, Stack, Text, Title } from "@mantine/core";

import type { EntityGraphNode } from "../../../domain/graph";
import { useUiConfig } from "../../../registry/UiConfigProvider";
import { formatMetricValue } from "../../../utils/metricFormat";

type Props = {
  readonly node: EntityGraphNode | null;
  readonly emptyLabel: string;
  readonly metricsLabel: string;
  readonly lineCountsLabel: string;
};

export function GraphEntityDetailPanel({
  node,
  emptyLabel,
  metricsLabel,
  lineCountsLabel,
}: Props) {
  const { registry } = useUiConfig();
  if (!node) {
    return <Text size="sm" c="dimmed">{emptyLabel}</Text>;
  }

  const groups = groupNodeMetrics(node, registry, lineCountsLabel, metricsLabel);

  return (
    <Paper withBorder radius="lg" p="md" bg="white">
      <Stack gap="md">
        <div>
          <Badge variant="light" color="teal" mb={6}>
            {registry?.entityKindLabel(node.entity.kind) ?? node.entity.kind}
          </Badge>
          <Title order={4}>{node.entity.label}</Title>
        </div>
        <SimpleGrid cols={{ base: 2, sm: 3, lg: 4 }} spacing="sm">
          {groups.map((group) => (
            <div className="ppi-metric-card" key={group.id}>
              <Text size="xs" c="dimmed" fw={650}>{group.group}</Text>
              <Text size="sm" fw={700} mt={2} mb="xs">{group.label}</Text>
              <Group gap="md" align="flex-start">
                {group.values.map((item) => (
                  <div key={item.label}>
                    {group.values.length > 1 || item.label !== group.label ? (
                      <Text size="xs" c="dimmed">{item.label}</Text>
                    ) : null}
                    <Text size="lg" fw={750} c="dark.8">{formatValue(item.value)}</Text>
                  </div>
                ))}
              </Group>
            </div>
          ))}
        </SimpleGrid>
      </Stack>
    </Paper>
  );
}

type Registry = ReturnType<typeof useUiConfig>["registry"];

function groupNodeMetrics(
  node: EntityGraphNode,
  registry: Registry,
  lineCountsLabel: string,
  metricsLabel: string,
) {
  const groups = new Map<string, {
    id: string;
    label: string;
    group: string;
    values: { label: string; value: unknown }[];
  }>();
  const lines = Object.entries(node.lineCounts ?? {});
  if (lines.length) {
    groups.set("lines", {
      id: "lines",
      label: lineCountsLabel,
      group: lineCountsLabel,
      values: lines.map(([id, value]) => ({
        label: registry?.lineCategoryLabel(id) ?? fallbackLabel(id),
        value,
      })),
    });
  }
  for (const metric of node.metrics) {
    const group = groups.get(metric.metricId) ?? {
      id: metric.metricId,
      label: registry?.metricLabel(metric.metricId) ?? fallbackLabel(metric.metricId),
      group: metricsLabel,
      values: [],
    };
    group.values.push({
      label: metric.aggregation ? fallbackLabel(metric.aggregation) : group.label,
      value: metric.value,
    });
    groups.set(metric.metricId, group);
  }
  return Array.from(groups.values());
}

function formatValue(value: unknown): string {
  if (typeof value === "number") return formatMetricValue(value);
  if (value === null || value === undefined) return "—";
  return String(value);
}

function fallbackLabel(value: string): string {
  return value.replace(/[_:.]+/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}
