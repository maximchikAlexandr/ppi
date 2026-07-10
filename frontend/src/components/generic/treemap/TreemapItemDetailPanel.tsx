/**
 * TreemapItemDetailPanel: renders the metric chips and attributes
 * of a TreemapItem. Driven entirely by the item's metricGroups and
 * attributes — no hardcoded metric ids, line counts, or paths.
 */
import { Paper, SimpleGrid, Stack, Text, Title } from "@mantine/core";

import { formatMetricValue } from "../../../utils/metricFormat";
import type { TreemapItem } from "../../../domain/treemap";

type Props = {
  readonly item: TreemapItem | null;
  readonly emptyLabel?: string;
};

export function TreemapItemDetailPanel({ item, emptyLabel }: Props) {
  if (!item) {
    return (
      <Paper withBorder radius="md" p="md" bg="#fbfcfd">
        <Text size="sm" c="dimmed">
          {emptyLabel ?? "Select an item to inspect its metrics."}
        </Text>
      </Paper>
    );
  }
  return (
    <Paper withBorder radius="md" p="md" bg="#fbfcfd">
      <Stack gap="sm">
        <Title order={3} size="h4">
          {item.entity.label}
        </Title>
        {item.metricGroups.length === 0 ? (
          <Text size="sm" c="dimmed">
            No metrics exposed for this item.
          </Text>
        ) : (
          <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="md">
            {item.metricGroups.map((g) => (
              <Stack key={g.id} gap={4}>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  {g.label}
                </Text>
                <Text size="lg" fw={700}>
                  {g.value === null || g.value === undefined
                    ? "—"
                    : typeof g.value === "number"
                      ? formatMetricValue(g.value)
                      : String(g.value)}
                </Text>
              </Stack>
            ))}
          </SimpleGrid>
        )}
        {Object.keys(item.attributes).length > 0 ? (
          <Stack gap={2}>
            {Object.entries(item.attributes).map(([k, v]) => (
              <Text key={k} size="xs" c="dimmed">
                {k}: {v === null || v === undefined ? "—" : String(v)}
              </Text>
            ))}
          </Stack>
        ) : null}
      </Stack>
    </Paper>
  );
}
