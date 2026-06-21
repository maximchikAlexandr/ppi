import { Checkbox, Group, Paper, Stack, Text } from "@mantine/core";

import { BRIGHTNESS_CRITERIA, type BrightnessCriterion } from "../registry/odooProfile";

type Props = {
  active: Set<BrightnessCriterion>;
  onChange: (next: Set<BrightnessCriterion>) => void;
};

export function BrightnessToolbar({ active, onChange }: Props) {
  return (
    <Paper withBorder radius="md" p="sm" style={{ width: "100%" }}>
      <Stack gap="xs">
        <Text size="sm" fw={600} c="dimmed">
          Module brightness criteria
        </Text>
        <Checkbox.Group
          value={[...active]}
          onChange={(values) => onChange(new Set(values as BrightnessCriterion[]))}
        >
          <Group gap="md">
            {BRIGHTNESS_CRITERIA.map(({ key, label }) => (
              <Checkbox key={key} value={key} label={label} />
            ))}
          </Group>
        </Checkbox.Group>
      </Stack>
    </Paper>
  );
}
