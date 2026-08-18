/**
 * GenericDataTable: renders a TableProjection using column definitions
 * and the GenericValueRenderer. Row actions are forwarded to the parent
 * via onAction; the parent owns the drilldown stack (single source of
 * truth, no duplicated state).
 */
import { useEffect, useMemo, useState } from "react";
import { Button, Group, MultiSelect, ScrollArea, Stack, Table, Text } from "@mantine/core";

import { GenericValueRenderer } from "../values/GenericValueRenderer";
import { t } from "../../../i18n";
import type { TableProjection } from "../../../domain/table";
import type { ActionDefinition } from "../../../domain/action";

type Props = {
  projection: TableProjection;
  onAction?: (action: ActionDefinition) => void;
};

export function GenericDataTable({ projection, onAction }: Props) {
  const [selectedColumnIds, setSelectedColumnIds] = useState<string[]>([]);
  useEffect(() => {
    setSelectedColumnIds(
      projection.columns.filter((column) => column.visibleByDefault).map((column) => column.id),
    );
  }, [projection.tableId, projection.commitId]);
  const columns = useMemo(
    () => projection.columns.filter(
      (column) => selectedColumnIds.includes(column.id) && projection.rows.some(
        (row) => hasDisplayValue(valueAtPath(row.cells, column.id)),
      ),
    ),
    [projection, selectedColumnIds],
  );
  const hasActions = projection.rows.some((row) => (row.actions?.length ?? 0) > 0);

  return (
    <Stack gap="xs">
      <Group justify="space-between" align="flex-end" wrap="wrap">
        <Text size="xs" c="dimmed">
          {t("tables.rowCount", "{{count}} rows", { count: projection.rows.length })}
        </Text>
        <MultiSelect
          label={t("tables.columns", "Columns")}
          data={projection.columns.map((column) => ({ value: column.id, label: column.label }))}
          value={selectedColumnIds}
          onChange={setSelectedColumnIds}
          searchable
          clearable
          w={280}
          size="xs"
        />
      </Group>
      <ScrollArea h={460} type="auto" offsetScrollbars>
      <Table
        striped
        highlightOnHover
        stickyHeader
        miw={Math.max(560, columns.length * 150 + (hasActions ? 120 : 0))}
        data-testid={`generic-table-${projection.tableId}`}
      >
        <Table.Thead>
          <Table.Tr>
            {columns.map((col) => (
              <Table.Th key={col.id} style={{ textAlign: col.align ?? "left" }}>
                {col.label}
              </Table.Th>
            ))}
            {hasActions ? (
              <Table.Th style={{ width: 120 }}>{t("tables.actions", "Actions")}</Table.Th>
            ) : null}
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
                    value={valueAtPath(row.cells, col.id)}
                    valueType={col.valueType}
                    metricId={col.metricId}
                    format={col.format}
                  />
                </Table.Td>
              ))}
              {hasActions ? <Table.Td>
                <Group gap="xs">
                  {(row.actions ?? []).map((a) => (
                    <Button
                      key={a.id}
                      size="compact-sm"
                      variant="light"
                      onClick={() => onAction?.(a)}
                    >
                      {a.label}
                    </Button>
                  ))}
                </Group>
              </Table.Td> : null}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      </ScrollArea>
    </Stack>
  );
}

function valueAtPath(cells: Record<string, unknown>, path: string): unknown {
  return path.split(".").reduce<unknown>((value, part) => {
    if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
    return (value as Record<string, unknown>)[part];
  }, cells);
}

function hasDisplayValue(value: unknown): boolean {
  return value !== null && value !== undefined && value !== "";
}
