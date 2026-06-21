import { Stack, Text } from "@mantine/core";

import type { MetricDistribution } from "../api/client";
import { formatMetricValue, formatStatsLine } from "../utils/metricFormat";

type Props = {
  dist: MetricDistribution | null | undefined;
};

export function MetricText({ dist }: Props) {
  return (
    <Stack gap={0}>
      <Text size="xs">{dist && dist.count ? `avg ${formatMetricValue(dist.mean)}` : "-"}</Text>
      <Text size="xs" c="dimmed">
        {formatStatsLine(dist)}
      </Text>
    </Stack>
  );
}
