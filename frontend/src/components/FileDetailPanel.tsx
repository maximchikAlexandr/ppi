import { Paper, SimpleGrid, Stack, Text, Title } from "@mantine/core";

import type { TreemapFile } from "./FileTreemap";
import { formatMetricValue } from "../utils/metricFormat";

type Props = {
  readonly file: TreemapFile | null;
};

export function FileDetailPanel({ file }: Props) {
  if (!file) {
    return (
      <Paper withBorder radius="md" p="md" bg="#fbfcfd">
        <Text size="sm" c="dimmed">
          Select a file on the treemap to inspect its complexity metrics.
        </Text>
      </Paper>
    );
  }
  const d = file.distributions;
  const lineCounts = file.line_counts ?? {};
  return (
    <Paper withBorder radius="md" p="md" bg="#fbfcfd">
      <Stack gap="sm">
        <Title order={3} size="h4">
          {file.module_name}/{file.relative_path}
        </Title>
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="md">
          <Stack gap={4}>
            <Text size="xs" tt="uppercase" fw={700} c="dimmed">Functions</Text>
            <Text size="lg" fw={700}>{String(lineCounts.function_count ?? 0)}</Text>
          </Stack>
          <Stack gap={4}>
            <Text size="xs" tt="uppercase" fw={700} c="dimmed">AST lines</Text>
            <Text size="lg" fw={700}>{String(lineCounts.jones_line_count ?? 0)}</Text>
          </Stack>
          {d?.cyclomatic && (
            <Stack gap={4}>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">Cyclomatic median</Text>
              <Text size="lg" fw={700}>{formatMetricValue(d.cyclomatic.median)}</Text>
            </Stack>
          )}
          {d?.cognitive && (
            <Stack gap={4}>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">Cognitive median</Text>
              <Text size="lg" fw={700}>{formatMetricValue(d.cognitive.median)}</Text>
            </Stack>
          )}
          {d?.jones && (
            <Stack gap={4}>
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">Jones median</Text>
              <Text size="lg" fw={700}>{formatMetricValue(d.jones.median)}</Text>
            </Stack>
          )}
        </SimpleGrid>
      </Stack>
    </Paper>
  );
}
