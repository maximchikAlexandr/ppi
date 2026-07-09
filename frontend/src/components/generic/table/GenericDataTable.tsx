/**
 * GenericDataTable: renders a TableProjection using column definitions
 * and the GenericValueRenderer. Row actions are forwarded to the parent
 * via onAction; the parent owns the drilldown stack (single source of
 * truth, no duplicated state).
 */
import { useMemo } from "react";
import { Group, Stack, Table, Text } from "@mantine/core";

import { GenericValueRenderer } from "../values/GenericValueRenderer";
import type { TableProjection } from "../../../domain/table";
import type { ActionDefinition } from "../../../domain/action";

type Props = {
  projection: TableProjection;
  onAction?: (action: ActionDefinition) => void;
};

export function GenericDataTable({ projection, onAction }: Props) {
  const columns = useMemo(() => projection.columns.filter((c) => c.visibleByDefault), [projection]);

  return (
    <Stack gap="xs">
      <Text fw={600}>{projection.title}</Text>
      <Table
        striped
        highlightOnHover
        withTableBorder
        withColumnBorders
        data-testid={`generic-table-${projection.tableId}`}
      >
        <Table.Thead>
          <Table.Tr>
            {columns.map((col) => (
              <Table.Th key={col.id} style={{ textAlign: col.align ?? "left" }}>
                {col.label}
              </Table.Th>
            ))}
            <Table.Th style={{ width: 120 }}>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {projection.rows.map((row) => (
            <Table.Tr key={row.id} data-testid="generic-row">
              {columns.map((col) => (
                <Table.Td
                  key={col.id}
                  style={{ textAlign: col.align ?? "left" }}
                  data-column-id={col.id}
                >
                  <GenericValueRenderer
                    value={row.cells[col.id]}
                    valueType={col.valueType}
                    metricId={col.metricId}
                    format={col.format}
                  />
                </Table.Td>
              ))}
              <Table.Td>
                <Group gap="xs">
                  {(row.actions ?? []).map((a) => (
                    <button
                      key={a.id}
                      type="button"
                      onClick={() => onAction?.(a)}
                    >
                      {a.label}
                    </button>
                  ))}
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Stack>
  );
}