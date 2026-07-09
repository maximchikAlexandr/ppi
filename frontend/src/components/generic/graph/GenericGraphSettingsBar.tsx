/**
 * GenericGraphSettingsBar: line-category filter chips + clear-focus
 * button. The full legacy GraphSettingsPanel (force tuning, display
 * state, layout commands) is mid-migration; this component covers
 * the only setting the new SnapshotPage actually consumes today.
 */
import { Group, MultiSelect, Stack, Text } from "@mantine/core";

import { t } from "../../../i18n";

export type GraphSettingsOption = {
  readonly id: string;
  readonly label: string;
};

type Props = {
  readonly lineCategoryOptions: readonly GraphSettingsOption[];
  readonly activeLineCategories: ReadonlySet<string>;
  readonly onLineCategoryChange: (next: Set<string>) => void;
  readonly onClearFocus?: () => void;
};

export function GenericGraphSettingsBar({
  lineCategoryOptions,
  activeLineCategories,
  onLineCategoryChange,
  onClearFocus,
}: Props) {
  const value = Array.from(activeLineCategories);
  return (
    <Stack gap="sm" data-testid="graph-settings-bar">
      <Text size="sm" fw={600}>
        {t("graph.settings.lineCategories", "Line categories")}
      </Text>
      <MultiSelect
        data={lineCategoryOptions.map((o) => ({ value: o.id, label: o.label }))}
        value={value}
        onChange={(next) => onLineCategoryChange(new Set(next))}
        searchable
        clearable
      />
      {onClearFocus ? (
        <Group justify="flex-end">
          <Text
            size="sm"
            c="blue"
            style={{ cursor: "pointer" }}
            onClick={onClearFocus}
            data-testid="graph-clear-focus"
          >
            {t("graph.settings.clearFocus", "Clear focus")}
          </Text>
        </Group>
      ) : null}
    </Stack>
  );
}
