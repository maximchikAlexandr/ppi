import { LineChart } from "@mantine/charts";
import { Group, Paper, Select, Stack, Table, Text, Title } from "@mantine/core";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  fetchCatalog,
  fetchCommits,
  fetchEdgeKindTimeseries,
  fetchRelationsDiff,
  fetchSnapshotModules,
  fetchTimeseries,
  type CommitRow,
  type EdgeKindPoint,
  type ModuleSnapshot,
  type RelationsDiffChange,
} from "../api/client";
import { CHART_CATEGORY_COLORS, edgeKindLabel, LINE_CATEGORIES } from "../registry/odooProfile";
import { formatMetricValue } from "../utils/metricFormat";

type ComplexityDiffRow = {
  module_name: string;
  cyclomatic_a: number;
  cyclomatic_b: number;
  cognitive_a: number;
  cognitive_b: number;
  jones_a: number;
  jones_b: number;
};

function buildComplexityDiff(modulesA: ModuleSnapshot[], modulesB: ModuleSnapshot[]): ComplexityDiffRow[] {
  const byNameB = new Map(modulesB.map((module) => [module.module_name, module]));
  return modulesA
    .filter((module) => byNameB.has(module.module_name))
    .map((module) => {
      const other = byNameB.get(module.module_name)!;
      return {
        module_name: module.module_name,
        cyclomatic_a: module.cyclomatic.median,
        cyclomatic_b: other.cyclomatic.median,
        cognitive_a: module.cognitive.median,
        cognitive_b: other.cognitive.median,
        jones_a: module.jones.median,
        jones_b: other.jones.median,
      };
    })
    .sort(
      (left, right) =>
        Math.abs(right.cyclomatic_b - right.cyclomatic_a)
        - Math.abs(left.cyclomatic_b - left.cyclomatic_a),
    );
}

export function AnalyticsPage() {
  const [commits, setCommits] = useState<CommitRow[]>([]);
  const [moduleNames, setModuleNames] = useState<string[]>([]);
  const [moduleName, setModuleName] = useState<string | null>(null);
  const [commitA, setCommitA] = useState<string | null>(null);
  const [commitB, setCommitB] = useState<string | null>(null);
  const [categoryChart, setCategoryChart] = useState<Record<string, number | string>[]>([]);
  const [categorySeries, setCategorySeries] = useState<{ name: string; label: string; color: string }[]>([]);
  const [fileCountSeries, setFileCountSeries] = useState<{ order: number; value: number }[]>([]);
  const [edgeKindPoints, setEdgeKindPoints] = useState<EdgeKindPoint[]>([]);
  const [diffChanges, setDiffChanges] = useState<RelationsDiffChange[]>([]);
  const [complexityDiff, setComplexityDiff] = useState<ComplexityDiffRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const bootstrapGeneration = useRef(0);
  const moduleGeneration = useRef(0);
  const diffGeneration = useRef(0);

  const commitOptions = useMemo(
    () =>
      commits.map((row) => ({
        value: row.commit_hash,
        label: `#${row.commit_order} ${row.commit_hash.slice(0, 8)}`,
      })),
    [commits],
  );

  const moduleOptions = useMemo(
    () => moduleNames.map((name) => ({ value: name, label: name })),
    [moduleNames],
  );

  const edgeKindChart = useMemo(() => {
    const orders = [...new Set(edgeKindPoints.map((point) => point.commit_order))].sort((a, b) => a - b);
    const kinds = [...new Set(edgeKindPoints.map((point) => point.kind))].sort();
    return orders.map((order) => {
      const row: Record<string, number | string> = { order };
      for (const kind of kinds) {
        row[kind] = edgeKindPoints.find((point) => point.commit_order === order && point.kind === kind)?.value ?? 0;
      }
      return row;
    });
  }, [edgeKindPoints]);

  const edgeKindSeries = useMemo(
    () =>
      [...new Set(edgeKindPoints.map((point) => point.kind))].sort().map((kind, index) => ({
        name: kind,
        label: edgeKindLabel(kind),
        color: CHART_CATEGORY_COLORS[index % CHART_CATEGORY_COLORS.length],
      })),
    [edgeKindPoints],
  );

  useEffect(() => {
    const generation = bootstrapGeneration.current + 1;
    bootstrapGeneration.current = generation;
    setError(null);
    Promise.all([fetchCommits(), fetchCatalog("module")])
      .then(([rows, catalog]) => {
        if (generation !== bootstrapGeneration.current) {
          return;
        }
        setCommits(rows);
        setModuleNames(catalog.names);
        setModuleName(catalog.names[0] ?? null);
        setCommitA(rows[0]?.commit_hash ?? null);
        setCommitB(rows[rows.length - 1]?.commit_hash ?? null);
      })
      .catch((err: Error) => {
        if (generation === bootstrapGeneration.current) {
          setError(err.message);
        }
      });
  }, []);

  useEffect(() => {
    if (!moduleName) {
      return;
    }
    const generation = moduleGeneration.current + 1;
    moduleGeneration.current = generation;
    setError(null);
    setCategoryChart([]);
    setFileCountSeries([]);
    Promise.all([
      fetchTimeseries({ level: "module", metric: "lines_by_category", name: moduleName }),
      fetchTimeseries({ level: "module", metric: "python_file_count", name: moduleName }),
      fetchEdgeKindTimeseries(),
    ])
      .then(([categories, fileCount, edgeKinds]) => {
        if (generation !== moduleGeneration.current) {
          return;
        }
        const orders = [
          ...new Set(categories.series.flatMap((series) => series.points.map((point) => point.commit_order))),
        ].sort((a, b) => a - b);
        const chartRows = orders.map((order) => {
          const row: Record<string, number | string> = { order };
          categories.series.forEach((series) => {
            const category = series.name.split("/").pop() ?? series.name;
            row[category] = Number(series.points.find((point) => point.commit_order === order)?.value ?? 0);
          });
          return row;
        });
        setCategoryChart(chartRows);
        setCategorySeries(
          LINE_CATEGORIES.map(({ key, label }, index) => ({
            name: key,
            label,
            color: CHART_CATEGORY_COLORS[index % CHART_CATEGORY_COLORS.length],
          })),
        );
        setFileCountSeries(
          fileCount.series[0]?.points.map((point) => ({
            order: point.commit_order,
            value: Number(point.value ?? 0),
          })) ?? [],
        );
        setEdgeKindPoints(edgeKinds.points);
      })
      .catch((err: Error) => {
        if (generation === moduleGeneration.current) {
          setError(err.message);
        }
      });
  }, [moduleName]);

  useEffect(() => {
    if (!commitA || !commitB) {
      setDiffChanges([]);
      setComplexityDiff([]);
      return;
    }
    const generation = diffGeneration.current + 1;
    diffGeneration.current = generation;
    setError(null);
    setDiffChanges([]);
    setComplexityDiff([]);
    Promise.all([
      fetchRelationsDiff(commitA, commitB),
      fetchSnapshotModules(commitA),
      fetchSnapshotModules(commitB),
    ])
      .then(([relations, modulesA, modulesB]) => {
        if (generation !== diffGeneration.current) {
          return;
        }
        setDiffChanges(relations.changes);
        setComplexityDiff(buildComplexityDiff(modulesA.modules, modulesB.modules));
      })
      .catch((err: Error) => {
        if (generation === diffGeneration.current) {
          setDiffChanges([]);
          setComplexityDiff([]);
          setError(err.message);
        }
      });
  }, [commitA, commitB]);

  return (
    <Stack gap="md">
      <Title order={3}>History analytics</Title>
      {error ? <Text c="red">{error}</Text> : null}
      <Group align="flex-end">
        <Select
          label="Module for series"
          data={moduleOptions}
          value={moduleName}
          onChange={setModuleName}
          searchable
          w={320}
        />
        <Select label="Commit A" data={commitOptions} value={commitA} onChange={setCommitA} searchable w={240} />
        <Select label="Commit B" data={commitOptions} value={commitB} onChange={setCommitB} searchable w={240} />
      </Group>
      <Paper withBorder p="md">
        <Title order={5} mb="sm">
          Lines by category ({moduleName})
        </Title>
        <LineChart h={240} data={categoryChart} dataKey="order" series={categorySeries} withLegend withTooltip />
      </Paper>
      <Paper withBorder p="md">
        <Title order={5} mb="sm">
          Python file count
        </Title>
        <LineChart
          h={220}
          data={fileCountSeries}
          dataKey="order"
          series={[{ name: "value", label: "files", color: "teal.6" }]}
        />
      </Paper>
      <Paper withBorder p="md">
        <Title order={5} mb="sm">
          Edge kind timeseries
        </Title>
        {edgeKindSeries.length ? (
          <LineChart h={240} data={edgeKindChart} dataKey="order" series={edgeKindSeries} withLegend withTooltip />
        ) : (
          <Text c="dimmed">No edge-kind history stored yet.</Text>
        )}
      </Paper>
      <Paper withBorder p="md">
        <Title order={5} mb="sm">
          Relations diff
        </Title>
        {!diffChanges.length ? (
          <Text c="dimmed">No relation changes between selected commits.</Text>
        ) : (
          <Table striped highlightOnHover withTableBorder>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Change</Table.Th>
                <Table.Th>Source</Table.Th>
                <Table.Th>Target</Table.Th>
                <Table.Th>Score A</Table.Th>
                <Table.Th>Score B</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {diffChanges.map((change) => (
                <Table.Tr key={`${change.change}-${change.source}-${change.target}`}>
                  <Table.Td>{change.change}</Table.Td>
                  <Table.Td>{change.source}</Table.Td>
                  <Table.Td>{change.target}</Table.Td>
                  <Table.Td>{change.score_a ?? "—"}</Table.Td>
                  <Table.Td>{change.score_b ?? "—"}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Paper>
      <Paper withBorder p="md">
        <Title order={5} mb="sm">
          Complexity diff (median)
        </Title>
        {!complexityDiff.length ? (
          <Text c="dimmed">No shared modules between selected commits.</Text>
        ) : (
          <Table striped highlightOnHover withTableBorder>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Module</Table.Th>
                <Table.Th>Cyclomatic A/B</Table.Th>
                <Table.Th>Cognitive A/B</Table.Th>
                <Table.Th>Jones A/B</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {complexityDiff.slice(0, 50).map((row) => (
                <Table.Tr key={row.module_name}>
                  <Table.Td>{row.module_name}</Table.Td>
                  <Table.Td>
                    {formatMetricValue(row.cyclomatic_a)} → {formatMetricValue(row.cyclomatic_b)}
                  </Table.Td>
                  <Table.Td>
                    {formatMetricValue(row.cognitive_a)} → {formatMetricValue(row.cognitive_b)}
                  </Table.Td>
                  <Table.Td>
                    {formatMetricValue(row.jones_a)} → {formatMetricValue(row.jones_b)}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Paper>
    </Stack>
  );
}
