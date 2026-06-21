import { LineChart } from "@mantine/charts";
import { Checkbox, Group, NumberInput, Paper, Select, SimpleGrid, Stack, Table, Text, Title } from "@mantine/core";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  fetchCommits,
  fetchEdges,
  fetchStructureTimeseries,
  type CommitRow,
  type EdgeRow,
  type StructurePoint,
} from "../api/client";
import { edgeKindLabel } from "../registry/odooProfile";

export function StructurePage() {
  const [commits, setCommits] = useState<CommitRow[]>([]);
  const [structurePoints, setStructurePoints] = useState<StructurePoint[]>([]);
  const [selectedCommit, setSelectedCommit] = useState<string | null>(null);
  const [edges, setEdges] = useState<EdgeRow[]>([]);
  const [includeZeroScore, setIncludeZeroScore] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [targetFilter, setTargetFilter] = useState<string | null>(null);
  const [kindFilter, setKindFilter] = useState<string | null>(null);
  const [minScore, setMinScore] = useState(1);
  const [loadingEdges, setLoadingEdges] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const edgesGeneration = useRef(0);
  const timeseriesGeneration = useRef(0);

  const commitOptions = useMemo(
    () =>
      commits.map((row) => ({
        value: row.commit_hash,
        label: `#${row.commit_order} ${row.commit_hash.slice(0, 8)} ${row.summary ?? ""}`,
      })),
    [commits],
  );

  const moduleOptions = useMemo(
    () =>
      [...new Set(edges.flatMap((edge) => [edge.source, edge.target]))]
        .sort((left, right) => left.localeCompare(right))
        .map((name) => ({ value: name, label: name })),
    [edges],
  );

  const kindOptions = useMemo(() => {
    const kinds = new Set<string>();
    for (const edge of edges) {
      for (const kind of Object.keys(edge.kinds ?? {})) {
        if ((edge.kinds?.[kind] ?? 0) > 0) {
          kinds.add(kind);
        }
      }
    }
    return [...kinds]
      .sort((left, right) => left.localeCompare(right))
      .map((kind) => ({ value: kind, label: edgeKindLabel(kind) }));
  }, [edges]);

  const filteredEdges = useMemo(
    () =>
      edges.filter((edge) => {
        if (sourceFilter && edge.source !== sourceFilter) {
          return false;
        }
        if (targetFilter && edge.target !== targetFilter) {
          return false;
        }
        if ((edge.score ?? 0) < minScore) {
          return false;
        }
        if (kindFilter) {
          return (edge.kinds?.[kindFilter] ?? 0) > 0;
        }
        return true;
      }),
    [edges, kindFilter, minScore, sourceFilter, targetFilter],
  );

  useEffect(() => {
    fetchCommits()
      .then(setCommits)
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    const generation = timeseriesGeneration.current + 1;
    timeseriesGeneration.current = generation;
    setError(null);
    fetchStructureTimeseries(includeZeroScore)
      .then((structure) => {
        if (generation !== timeseriesGeneration.current) {
          return;
        }
        setStructurePoints(structure.points);
        setSelectedCommit((current) => {
          if (current && structure.points.some((point) => point.commit_hash === current)) {
            return current;
          }
          return (
            [...structure.points].reverse().find((point) => point.edge_count > 0)?.commit_hash
            ?? commits[commits.length - 1]?.commit_hash
            ?? null
          );
        });
      })
      .catch((err: Error) => {
        if (generation === timeseriesGeneration.current) {
          setError(err.message);
        }
      });
  }, [commits, includeZeroScore]);

  useEffect(() => {
    if (!selectedCommit) {
      return;
    }
    const generation = edgesGeneration.current + 1;
    edgesGeneration.current = generation;
    setLoadingEdges(true);
    setError(null);
    setEdges([]);
    fetchEdges(selectedCommit, includeZeroScore)
      .then((payload) => {
        if (generation === edgesGeneration.current) {
          setEdges(payload.edges);
        }
      })
      .catch((err: Error) => {
        if (generation === edgesGeneration.current) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (generation === edgesGeneration.current) {
          setLoadingEdges(false);
        }
      });
  }, [includeZeroScore, selectedCommit]);

  const chartData = structurePoints.map((point) => ({
    order: point.commit_order,
    edge_count: point.edge_count,
    total_score: point.total_score,
  }));

  const selectedPoint = structurePoints.find((point) => point.commit_hash === selectedCommit);

  return (
    <Stack gap="md">
      <Title order={3}>Structure over time</Title>
      {error ? <Text c="red">{error}</Text> : null}
      <Checkbox
        label="Include zero-score edges"
        checked={includeZeroScore}
        onChange={(event) => setIncludeZeroScore(event.currentTarget.checked)}
      />
      <Paper withBorder p="md">
        <Title order={4} mb="md">
          Coupling edges per commit
        </Title>
        {!chartData.length ? (
          <Text c="dimmed">No structure history stored yet.</Text>
        ) : (
          <LineChart
            h={280}
            data={chartData}
            dataKey="order"
            series={[
              { name: "edge_count", label: "Edges", color: "teal.6" },
              { name: "total_score", label: "Total score", color: "grape.6" },
            ]}
            curveType="monotone"
            withLegend
            withTooltip
          />
        )}
      </Paper>
      <Group align="flex-end">
        <Select
          label="Commit"
          data={commitOptions}
          value={selectedCommit}
          onChange={setSelectedCommit}
          searchable
          w={420}
        />
        <Text size="sm" c="dimmed">
          Chart edges: {selectedPoint?.edge_count ?? "—"} | Table rows: {filteredEdges.length} / {edges.length}
        </Text>
      </Group>
      <Paper withBorder p="md">
        <Title order={4} mb="sm">
          Coupling edges at selected commit
        </Title>
        <SimpleGrid cols={{ base: 1, md: 4 }} spacing="md" mb="md">
          <Select
            label="Source module"
            placeholder="All modules"
            clearable
            searchable
            data={moduleOptions}
            value={sourceFilter}
            onChange={setSourceFilter}
          />
          <Select
            label="Target module"
            placeholder="All modules"
            clearable
            searchable
            data={moduleOptions}
            value={targetFilter}
            onChange={setTargetFilter}
          />
          <Select
            label="Kind"
            placeholder="All kinds"
            clearable
            searchable
            data={kindOptions}
            value={kindFilter}
            onChange={setKindFilter}
          />
          <NumberInput
            label="Min score"
            min={0}
            value={minScore}
            onChange={(value) => setMinScore(typeof value === "number" ? value : 0)}
          />
        </SimpleGrid>
        {!loadingEdges && !filteredEdges.length ? (
          <Text c="dimmed">No coupling edges match the current filters.</Text>
        ) : loadingEdges ? (
          <Text c="dimmed">Loading coupling edges…</Text>
        ) : (
          <Table striped highlightOnHover withTableBorder>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Source</Table.Th>
                <Table.Th>Target</Table.Th>
                <Table.Th>Score</Table.Th>
                <Table.Th>Kind occ.</Table.Th>
                <Table.Th>Evidence</Table.Th>
                <Table.Th>Breakdown</Table.Th>
                <Table.Th>Kinds</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {filteredEdges.map((edge) => (
                <Table.Tr key={`${edge.source}-${edge.target}`}>
                  <Table.Td>{edge.source}</Table.Td>
                  <Table.Td>{edge.target}</Table.Td>
                  <Table.Td>{edge.score}</Table.Td>
                  <Table.Td>{edge.kind_occurrence_count ?? 0}</Table.Td>
                  <Table.Td>{edge.evidence_count ?? "—"}</Table.Td>
                  <Table.Td>
                    {edge.breakdown
                      ? `${edge.breakdown.total} (mr=${edge.breakdown.model_reuse})`
                      : "—"}
                  </Table.Td>
                  <Table.Td>
                    {Object.entries(edge.kinds ?? {})
                      .sort((left, right) => right[1] - left[1])
                      .map(([kind, count]) => `${edgeKindLabel(kind)} (${count})`)
                      .join(", ") || "—"}
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
