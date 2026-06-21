import { Paper, Stack, Text } from "@mantine/core";

import { formatCodeLines } from "../utils/metricFormat";

type Props = {
  total: number;
  selectedLabels: string[];
  loading?: boolean;
};

export function VisibleLinesSummary({ total, selectedLabels, loading = false }: Props) {
  return (
    <Paper withBorder radius="md" p="md" bg="#fbfcfd">
      <Stack gap={4}>
        <Text size="xs" tt="uppercase" fw={700} c="dimmed">
          Visible code lines
        </Text>
        <Text size="xl" fw={700}>
          {loading ? "…" : formatCodeLines(total)}
        </Text>
        <Text size="xs" c="dimmed">
          {selectedLabels.length
            ? `Selected categories: ${selectedLabels.join(", ")}`
            : "No line categories selected."}
        </Text>
      </Stack>
    </Paper>
  );
}
