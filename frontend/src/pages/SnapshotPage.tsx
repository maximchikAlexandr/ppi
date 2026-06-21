import { Accordion, Center, Checkbox, Code, Group, Loader, Paper, Select, Stack, Text, Title } from "@mantine/core";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  fetchCommits,
  fetchFailures,
  fetchGraph,
  fetchSnapshotFiles,
  fetchSnapshotModules,
  type CommitRow,
  type EdgeRow,
  type FailureRow,
  type FileSnapshot,
  type GraphEdge,
  type GraphNode,
  type ModuleSnapshot,
} from "../api/client";
import { BrightnessToolbar } from "../components/BrightnessToolbar";
import { FileDetailPanel } from "../components/FileDetailPanel";
import { FileTreemap } from "../components/FileTreemap";
import { LineCategoryToolbar } from "../components/LineCategoryToolbar";
import { ManifestDependsView } from "../components/ManifestDependsView";
import { ModuleDetailPanel } from "../components/ModuleDetailPanel";
import { ModuleGraph } from "../components/ModuleGraph";
import { ParseFailureView } from "../components/ParseFailureView";
import { VisibleLinesSummary } from "../components/VisibleLinesSummary";
import { EdgePointsTable, FileComplexityTable, ModuleLinesTable } from "../components/ReportTables";
import { useAppNavigation } from "../navigation";
import {
  type BrightnessCriterion,
  DEFAULT_BRIGHTNESS_CRITERIA,
  DEFAULT_LINE_CATEGORIES,
  type LineCategoryKey,
  LINE_CATEGORIES,
  lineCategoryTotal,
  moduleCouplingStats,
} from "../registry/odooProfile";
import { formatCodeLines } from "../utils/metricFormat";

function graphEdgesToRows(edges: GraphEdge[], commitHash: string): EdgeRow[] {
  return edges.map((edge) => ({
    source: edge.source,
    target: edge.target,
    score: edge.score,
    kinds: edge.kinds ?? {},
    kind_occurrence_count: edge.kind_occurrence_count,
    evidence_count: edge.evidence_count,
    breakdown: edge.breakdown,
    commit_hash: edge.commit_hash ?? commitHash,
  }));
}

function LoadingPanel({ label }: { label: string }) {
  return (
    <Paper withBorder radius="md" p="xl" bg="#fbfcfd">
      <Center>
        <Stack align="center" gap="xs">
          <Loader size="sm" />
          <Text size="sm" c="dimmed">
            {label}
          </Text>
        </Stack>
      </Center>
    </Paper>
  );
}

export function SnapshotPage() {
  const {
    pendingSnapshot,
    clearPendingSnapshot,
  } = useAppNavigation();
  const [commits, setCommits] = useState<CommitRow[]>([]);
  const [selectedCommit, setSelectedCommit] = useState<string | null>(null);
  const [modules, setModules] = useState<ModuleSnapshot[]>([]);
  const [files, setFiles] = useState<FileSnapshot[]>([]);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [fullEdges, setFullEdges] = useState<EdgeRow[]>([]);
  const [failures, setFailures] = useState<FailureRow[]>([]);
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileSnapshot | null>(null);
  const [hoveredFile, setHoveredFile] = useState<FileSnapshot | null>(null);
  const [lineCategories, setLineCategories] = useState<Set<LineCategoryKey>>(
    () => new Set(DEFAULT_LINE_CATEGORIES),
  );
  const [brightness, setBrightness] = useState<Set<BrightnessCriterion>>(
    () => new Set(DEFAULT_BRIGHTNESS_CRITERIA),
  );
  const [includeZeroScore, setIncludeZeroScore] = useState(false);
  const [loadingCommits, setLoadingCommits] = useState(true);
  const [loadingSnapshot, setLoadingSnapshot] = useState(false);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [openSections, setOpenSections] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const snapshotGeneration = useRef(0);
  const graphGeneration = useRef(0);

  const commitOptions = useMemo(
    () =>
      commits.map((row) => ({
        value: row.commit_hash,
        label: `#${row.commit_order} ${row.commit_hash.slice(0, 8)} ${row.summary ?? ""}`,
      })),
    [commits],
  );

  const moduleFiles = useMemo(
    () => (selectedModule ? files.filter((file) => file.module_name === selectedModule) : []),
    [files, selectedModule],
  );

  const moduleDetail = useMemo(
    () => modules.find((module) => module.module_name === selectedModule) ?? null,
    [modules, selectedModule],
  );

  const edgeRows = fullEdges;

  const selectedCouplingStats = useMemo(
    () =>
      selectedModule && fullEdges.length
        ? moduleCouplingStats(selectedModule, fullEdges)
        : null,
    [fullEdges, selectedModule],
  );

  const visibleLinesTotal = useMemo(
    () =>
      modules.reduce(
        (sum, module) => sum + lineCategoryTotal(module.line_categories, lineCategories),
        0,
      ),
    [lineCategories, modules],
  );

  const selectedCategoryLabels = useMemo(
    () => LINE_CATEGORIES.filter(({ key }) => lineCategories.has(key)).map(({ label }) => label),
    [lineCategories],
  );

  const moduleOptions = useMemo(
    () => [...new Set(modules.map((module) => module.module_name))].sort((left, right) => left.localeCompare(right)),
    [modules],
  );

  const activeFile = selectedFile ?? hoveredFile;

  const moduleVisibleLines = useMemo(
    () =>
      moduleDetail
        ? lineCategoryTotal(moduleDetail.line_categories, lineCategories)
        : 0,
    [lineCategories, moduleDetail],
  );

  useEffect(() => {
    if (!pendingSnapshot) {
      return;
    }
    setSelectedCommit(pendingSnapshot.commitHash);
    if (pendingSnapshot.tab) {
      setOpenSections([pendingSnapshot.tab]);
    }
    clearPendingSnapshot();
  }, [clearPendingSnapshot, pendingSnapshot]);

  useEffect(() => {
    setLoadingCommits(true);
    fetchCommits()
      .then((rows) => {
        setCommits(rows);
        setSelectedCommit((current) => current ?? rows[rows.length - 1]?.commit_hash ?? null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoadingCommits(false));
  }, []);

  useEffect(() => {
    if (!selectedCommit) {
      return;
    }
    const generation = snapshotGeneration.current + 1;
    snapshotGeneration.current = generation;
    setSelectedModule(null);
    setSelectedFile(null);
    setHoveredFile(null);
    setModules([]);
    setFiles([]);
    setFailures([]);
    setGraphNodes([]);
    setGraphEdges([]);
    setFullEdges([]);
    setLoadingSnapshot(true);
    setError(null);
    Promise.all([
      fetchSnapshotModules(selectedCommit),
      fetchSnapshotFiles(selectedCommit),
      fetchFailures(selectedCommit),
    ])
      .then(([modulePayload, filePayload, failurePayload]) => {
        if (generation !== snapshotGeneration.current) {
          return;
        }
        setModules(modulePayload.modules);
        setFiles(filePayload.files);
        setFailures(failurePayload.failures);
      })
      .catch((err: Error) => {
        if (generation === snapshotGeneration.current) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (generation === snapshotGeneration.current) {
          setLoadingSnapshot(false);
        }
      });
  }, [selectedCommit]);

  useEffect(() => {
    if (!selectedCommit) {
      return;
    }
    const generation = graphGeneration.current + 1;
    graphGeneration.current = generation;
    setGraphNodes([]);
    setGraphEdges([]);
    setFullEdges([]);
    setLoadingGraph(true);
    setError(null);
    fetchGraph(selectedCommit, includeZeroScore)
      .then((graphPayload) => {
        if (generation !== graphGeneration.current) {
          return;
        }
        setGraphNodes(graphPayload.nodes);
        setGraphEdges(graphPayload.edges);
        setFullEdges(graphEdgesToRows(graphPayload.edges, graphPayload.commit_hash));
      })
      .catch((err: Error) => {
        if (generation === graphGeneration.current) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (generation === graphGeneration.current) {
          setLoadingGraph(false);
        }
      });
  }, [includeZeroScore, selectedCommit]);

  function onSelectModule(name: string | null) {
    setSelectedModule(name);
    setSelectedFile(null);
    setHoveredFile(null);
  }

  return (
    <Stack gap="md">
      <Title order={3}>Odoo report snapshot</Title>
      {error ? <Text c="red">{error}</Text> : null}
      <Group align="flex-end" wrap="wrap">
        <Select
          label="Commit"
          data={commitOptions}
          value={selectedCommit}
          onChange={setSelectedCommit}
          searchable
          w={420}
          disabled={loadingCommits}
          rightSection={loadingCommits ? <Loader size="xs" /> : undefined}
        />
        <Checkbox
          label="Include zero-score edges"
          checked={includeZeroScore}
          onChange={(event) => setIncludeZeroScore(event.currentTarget.checked)}
        />
        <Text size="sm" c="dimmed">
          Visible edges: {loadingGraph ? "…" : edgeRows.length}
        </Text>
      </Group>
      <VisibleLinesSummary
        total={visibleLinesTotal}
        selectedLabels={selectedCategoryLabels}
        loading={loadingSnapshot}
      />

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          Graph view
        </Title>
        <Text size="sm" c="dimmed" mb="md">
          Edge points formula:{" "}
          <Code>model reuse</Code> = 1 point per relation,{" "}
          <Code>extension/method</Code> = 1 point per model extension or method call,{" "}
          <Code>view</Code> = 1 point per view link,{" "}
          <Code>field/property</Code> = 1 point per field/property access.
          Edge thickness and attraction reflect total points. Drag any node to move the graph.
        </Text>
        <ModuleGraph
          nodes={graphNodes}
          edges={graphEdges}
          lineCategories={lineCategories}
          brightnessCriteria={brightness}
          selectedModule={selectedModule}
          onSelectModule={onSelectModule}
          loading={loadingGraph}
        />
        <Stack gap="md" mt="md">
          <LineCategoryToolbar active={lineCategories} onChange={setLineCategories} />
          <BrightnessToolbar active={brightness} onChange={setBrightness} />
          {loadingSnapshot && selectedModule && !moduleDetail ? (
            <LoadingPanel label="Loading module details…" />
          ) : (
            <ModuleDetailPanel
              module={moduleDetail}
              brightnessCriteria={brightness}
              couplingStats={selectedCouplingStats}
            />
          )}
        </Stack>
      </Paper>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          Module file map
        </Title>
        <Text size="sm" c="dimmed" mb="md">
          Treemap of files inside the selected module. Tile area is proportional to line count.
        </Text>
        <Text size="sm" mb="sm" c={selectedModule ? undefined : "dimmed"}>
          {selectedModule
            ? `Module ${selectedModule}: ${formatCodeLines(moduleVisibleLines)} visible lines`
            : "Click a module on the graph to see its file map."}
        </Text>
        {selectedModule ? (
          loadingSnapshot ? (
            <LoadingPanel label="Loading module files…" />
          ) : (
            <>
              <Stack gap="md">
                <FileTreemap
                  files={moduleFiles}
                  lineCategories={lineCategories}
                  selectedPath={
                    selectedFile ? `${selectedFile.module_name}/${selectedFile.relative_path}` : null
                  }
                  onSelect={setSelectedFile}
                  onHover={setHoveredFile}
                />
                <FileDetailPanel file={activeFile} />
              </Stack>
            </>
          )
        ) : (
          <FileDetailPanel file={null} />
        )}
      </Paper>

      <Accordion
        multiple
        variant="contained"
        value={openSections}
        onChange={(value) => setOpenSections(Array.isArray(value) ? value : value ? [value] : [])}
      >
        <Accordion.Item value="lines">
          <Accordion.Control>Module code lines</Accordion.Control>
          <Accordion.Panel>
            {loadingSnapshot ? (
              <LoadingPanel label="Loading module lines…" />
            ) : (
              <ModuleLinesTable modules={modules} />
            )}
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value="complexity">
          <Accordion.Control>Python file complexity</Accordion.Control>
          <Accordion.Panel>
            {loadingSnapshot ? (
              <LoadingPanel label="Loading file complexity…" />
            ) : (
              <FileComplexityTable files={files} />
            )}
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value="edges">
          <Accordion.Control>Graph edge points</Accordion.Control>
          <Accordion.Panel>
            {loadingGraph ? (
              <LoadingPanel label="Loading edge points…" />
            ) : selectedCommit ? (
              <EdgePointsTable
                edges={edgeRows}
                commit={selectedCommit}
                includeZeroScore={includeZeroScore}
                moduleOptions={moduleOptions}
              />
            ) : null}
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value="manifest">
          <Accordion.Control>Manifest depends</Accordion.Control>
          <Accordion.Panel>
            {loadingSnapshot ? (
              <LoadingPanel label="Loading manifest data…" />
            ) : (
              <ManifestDependsView modules={modules} />
            )}
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value="failures">
          <Accordion.Control>Parse failures</Accordion.Control>
          <Accordion.Panel>
            {loadingSnapshot ? (
              <LoadingPanel label="Loading parse failures…" />
            ) : (
              <ParseFailureView failures={failures} />
            )}
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}
