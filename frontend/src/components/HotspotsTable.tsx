import { Paper, Table, Text, Title } from "@mantine/core";

import type { HotspotItem } from "../domain/query";
import { t } from "../i18n";

type HotspotsTableProps = {
  readonly title: string;
  readonly items: readonly HotspotItem[];
  readonly showGrowth: boolean;
};

export function HotspotsTable({ title, items, showGrowth }: HotspotsTableProps) {
  const displayItems = showGrowth ? items.filter((item) => item.growth != null) : items;

  return (
    <Paper withBorder p="md">
      <Title order={4} mb="md">
        {title}
      </Title>
      {!displayItems.length ? (
        <Text c="dimmed">{t("dashboard.hotspots.empty", "No hotspot data yet.")}</Text>
      ) : (
        <Table striped highlightOnHover withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>{t("dashboard.hotspots.name", "Name")}</Table.Th>
              <Table.Th>{t("dashboard.hotspots.value", "Current")}</Table.Th>
              {showGrowth ? (
                <Table.Th>{t("dashboard.hotspots.change", "Growth")}</Table.Th>
              ) : null}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {displayItems.map((item) => (
              <Table.Tr key={item.entity.id}>
                <Table.Td>{item.entity.label}</Table.Td>
                <Table.Td>{item.current?.toFixed(2) ?? "—"}</Table.Td>
                {showGrowth ? (
                  <Table.Td>{item.growth != null ? item.growth.toFixed(2) : "—"}</Table.Td>
                ) : null}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Paper>
  );
}
