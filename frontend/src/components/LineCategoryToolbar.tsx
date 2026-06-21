import { Checkbox, Group, Paper, Stack, Text } from "@mantine/core";

import { LINE_CATEGORIES, type LineCategoryKey } from "../registry/odooProfile";

type Props = {
  active: Set<LineCategoryKey>;
  onChange: (next: Set<LineCategoryKey>) => void;
};

export function LineCategoryToolbar({ active, onChange }: Props) {
  return (
    <Paper withBorder radius="md" p="sm" style={{ width: "100%" }}>
      <Stack gap="xs">
        <Text size="sm" fw={600} c="dimmed">
          Lines displayed inside node
        </Text>
        <Checkbox.Group
          value={[...active]}
          onChange={(values) => onChange(new Set(values as LineCategoryKey[]))}
        >
          <Group gap="md">
            {LINE_CATEGORIES.map(({ key, label }) => (
              <Checkbox key={key} value={key} label={label} />
            ))}
          </Group>
        </Checkbox.Group>
      </Stack>
    </Paper>
  );
}
