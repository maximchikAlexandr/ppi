import { Badge, Group, Paper, SimpleGrid, Stack, Text, Title } from "@mantine/core";

import type { ModuleSnapshot } from "../api/client";
import {
  BRIGHTNESS_CRITERIA,
  type BrightnessCriterion,
  LINE_CATEGORIES,
  type ModuleCouplingStats,
} from "../registry/odooProfile";
import { formatCodeLines } from "../utils/metricFormat";
import { DistributionBlock } from "./DistributionBlock";

type Props = {
  module: ModuleSnapshot | null;
  brightnessCriteria: Set<BrightnessCriterion>;
  couplingStats?: ModuleCouplingStats | null;
};

export function ModuleDetailPanel({ module, brightnessCriteria, couplingStats }: Props) {
  if (!module) {
    return (
      <Paper withBorder radius="md" p="md" bg="#fbfcfd">
        <Text size="sm" c="dimmed">
          Click a module to inspect its line and complexity metrics.
        </Text>
      </Paper>
    );
  }
  const activeBrightnessLabels = BRIGHTNESS_CRITERIA.filter(({ key }) => brightnessCriteria.has(key)).map(
    ({ label }) => label,
  );
  return (
    <Paper withBorder radius="md" p="md" bg="#fbfcfd">
      <Stack gap="sm">
        <Group justify="space-between" align="flex-start">
          <Title order={3} size="h4">
            {module.module_name}
          </Title>
          <Badge color="teal" variant="light">
            {activeBrightnessLabels.length ? activeBrightnessLabels.join(", ") : "No brightness criteria"}
          </Badge>
        </Group>
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="md">
          <DistributionBlock label="Cyclomatic" dist={module.cyclomatic} />
          <DistributionBlock label="Cognitive" dist={module.cognitive} />
          <DistributionBlock label="Jones nodes/line" dist={module.jones} />
          <Stack gap={4}>
            <Text size="xs" tt="uppercase" fw={700} c="dimmed">
              Method count
            </Text>
            <Text size="lg" fw={700}>
              {formatCodeLines(module.cyclomatic.count)}
            </Text>
            <Text size="xs" c="dimmed">
              Functions/methods counted by cyclomatic analysis
            </Text>
          </Stack>
          <Stack gap={4}>
            <Text size="xs" tt="uppercase" fw={700} c="dimmed">
              Code lines
            </Text>
            <Text size="lg" fw={700}>
              {formatCodeLines(module.line_categories.python_lines ?? 0)}
            </Text>
            <Text size="xs" c="dimmed">
              Production Python lines only, tests excluded
            </Text>
          </Stack>
          <Stack gap={4}>
            <Text size="xs" tt="uppercase" fw={700} c="dimmed">
              Python file count
            </Text>
            <Text size="lg" fw={700}>
              {formatCodeLines(module.python_file_count)}
            </Text>
            <Text size="xs" c="dimmed">
              Production Python files only, tests excluded
            </Text>
          </Stack>
        </SimpleGrid>
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
          <Text size="sm">Total lines: {formatCodeLines(module.total_lines)}</Text>
          {LINE_CATEGORIES.map(({ key, label }) => (
            <Text key={key} size="sm">
              {label}: {formatCodeLines(module.line_categories[key] ?? 0)}
            </Text>
          ))}
          <Text size="sm">Score in: {module.score_in}</Text>
          <Text size="sm">Score out: {module.score_out}</Text>
          {couplingStats ? (
            <>
              <Text size="sm">Outgoing edges: {couplingStats.outgoing_edges}</Text>
              <Text size="sm">Incoming edges: {couplingStats.incoming_edges}</Text>
              <Text size="sm">Private calls: {couplingStats.private_calls}</Text>
            </>
          ) : null}
          <Text size="sm">Parse errors: {module.python_complexity_parse_errors}</Text>
        </SimpleGrid>
        <Stack gap={4}>
          <Text size="sm">Declared models: {module.declared_models.join(", ") || "—"}</Text>
          <Text size="sm">Inherited models: {module.inherited_models.join(", ") || "—"}</Text>
          {module.manifest_depends ? (
            <Text size="sm">Manifest depends: {module.manifest_depends.join(", ") || "—"}</Text>
          ) : null}
        </Stack>
      </Stack>
    </Paper>
  );
}
