import { Group, Loader, Paper, Select, Stack, Text, Title } from "@mantine/core";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  listCommitsV1,
  getUiConfigV1,
  getGraphV1,
  getTableV1,
  type CommitSummaryV1,
} from "../api/publicApi";
import type { EntityGraphModel } from "../domain/graph";
import { FileDetailPanel } from "../components/FileDetailPanel";
import { FileTreemap } from "../components/FileTreemap";
import { GraphSettingsPanel } from "../components/GraphSettingsPanel";
import { ModuleGraph } from "../components/ModuleGraph";
import { VisibleLinesSummary } from "../components/VisibleLinesSummary";
import type { TreemapFile } from "../components/FileTreemap";
import { t } from "../i18n";
import { useSnapshotGraphExplorer } from "../legacy/legacySnapshotGraphExplorer";
import { useAppNavigation } from "../navigation";
import { lineCategoryTotal } from "../legacy/graphUiHelpers";
import { toCommitSelectOptions } from "../transforms/commitOptions";
import { formatCommitDate } from "../transforms/commitDate";
import {
  resolveGraphSelection,
  resolveProjectStorageKey,
} from "../transforms/snapshotTransforms";
import { formatCodeLines } from "../utils/metricFormat";
import { LoadingPanel } from "../components/LoadingPanel";

type UiConfigState = {
  schemaVersion: number;
  graph: {
    edgeTypes: readonly { id: string; label: string; defaultEnabled: boolean }[];
    lineCategories: readonly { id: string; label: string; defaultEnabled: boolean }[];
    brightnessMetrics: readonly { id: string; label: string; defaultEnabled: boolean }[];
    nodeSizeMetrics: readonly { id: string; label: string; defaultEnabled: boolean }[];
    linkThicknessMetrics: readonly { id: string; label: string; defaultEnabled: boolean }[];
  };
};

export function SnapshotPage() {
  const { selectedCommit, setSelectedCommit } = useAppNavigation();
  const [commits, setCommits] = useState<readonly CommitSummaryV1[]>([]);
  const [filesTable, setFilesTable] = useState<{ rows: Array<Record<string, unknown>> } | null>(null);
  const [graphModel, setGraphModel] = useState<EntityGraphModel | null>(null);
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<TreemapFile | null>(null);
  const [hoveredFile, setHoveredFile] = useState<TreemapFile | null>(null);
  const [lineCategories, setLineCategories] = useState<Set<string>>(new Set());
  const [brightness, setBrightness] = useState<Set<string>>(new Set());
  const [loadingCommits, setLoadingCommits] = useState(true);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [focusNotice, setFocusNotice] = useState<string | null>(null);
  const [projectKey] = useState<string | null>(() =>
    resolveProjectStorageKey(null, null, window.location.origin + window.location.pathname),
  );
  const [uiConfig, setUiConfig] = useState<UiConfigState | null>(null);

  const graphGeneration = useRef(0);
  const defaultEnabledEdgeKinds = useMemo(
    () => Object.fromEntries((uiConfig?.graph.edgeTypes ?? []).map((option) => [option.id, true])),
    [uiConfig],
  );

  const commitOptions = useMemo(() => toCommitSelectOptions(commits), [commits]);
  const graphExplorer = useSnapshotGraphExplorer({
    commits,
    selectedCommit,
    setSelectedCommit,
    graphNodes: (graphModel?.nodes ?? []).map((n) => ({
      module_name: n.entity.id,
      total_lines: 0,
      metrics: Object.fromEntries(n.metrics.map((m) => [m.metricId, Number(m.value ?? 0)])),
      line_counts: n.lineCounts ?? {},
    })),
    graphEdges: (graphModel?.edges ?? []).map((e) => ({
      source: e.source.id,
      target: e.target.id,
      score: 0,
      kinds: { [e.relationTypeId]: 1 },
      kind_occurrence_count: 1,
      commit_hash: e.id,
    })),
    selectedModule,
    setSelectedModule,
    setSelectedFile,
    setHoveredFile,
    projectKey,
    loadingGraph,
    setFocusNotice,
    defaultEnabledEdgeKinds,
  });
  const {
    edgeKindMeta,
    emptyNotice,
    filterResult,
    focusModuleRef,
    graphPanelProps,
    maxEffectiveScore,
    onSelectModule,
    resetLayoutState,
    selectedCommitDisabled,
    setFilter,
    settings,
  } = graphExplorer;

  const selectedCommitMeta = useMemo(
    () => commits.find((row) => row.commitId === selectedCommit) ?? null,
    [commits, selectedCommit],
  );
  const commitDateLabel = useMemo(
    () => formatCommitDate(selectedCommitMeta?.authoredAt ?? null),
    [selectedCommitMeta],
  );
  const edgeKindConfigLabels = useMemo(() => {
    const map: Record<string, string> = {};
    for (const opt of uiConfig?.graph.edgeTypes ?? []) {
      map[opt.id] = opt.label;
    }
    return map;
  }, [uiConfig]);

  const selectedCategoryLabels = useMemo(
    () =>
      (uiConfig?.graph.lineCategories ?? [])
        .filter((o) => lineCategories.has(o.id))
        .map((o) => o.label),
    [lineCategories, uiConfig],
  );

  const moduleDetail = useMemo(() => {
    if (!selectedModule) return null;
    return (graphModel?.nodes ?? []).find((n) => n.entity.id === selectedModule) ?? null;
  }, [graphModel, selectedModule]);

  const moduleVisibleLines = useMemo(
    () =>
      moduleDetail ? lineCategoryTotal(
        (moduleDetail.lineCounts ?? {}) as Record<string, number>,
        lineCategories,
      ) : 0,
    [lineCategories, moduleDetail],
  );
  const visibleCodeLines = useMemo(
    () =>
      filterResult.nodes.reduce(
        (total, node) => total + lineCategoryTotal(node.line_counts, lineCategories),
        0,
      ),
    [filterResult.nodes, lineCategories],
  );

  const moduleFiles = useMemo<TreemapFile[]>(() => {
    if (!filesTable || !selectedModule) return [];
    return filesTable.rows
      .filter((r) => String(r.id ?? "").startsWith(`${selectedModule}/`))
      .map((r) => {
        const cells = r as { relative_path?: string; metrics?: Record<string, number>; line_counts?: Record<string, number> };
        const relativePath = String(cells.relative_path ?? "");
        const metrics = (cells.metrics ?? {}) as Record<string, number>;
        const lineCounts = (cells.line_counts ?? {}) as Record<string, number>;
        const parts = relativePath.split("/");
        return {
          module_name: selectedModule,
          relative_path: relativePath,
          line_category_id: "",
          lines: Number(lineCounts.lines ?? metrics.lines ?? metrics.total_lines ?? 0),
          top_folder: parts.length > 1 ? parts[0] : ".",
          metrics,
          line_counts: lineCounts,
          distributions: {} as Record<string, { median: number; mean: number; count: number; p95: number; max: number }>,
        } satisfies TreemapFile;
      });
  }, [filesTable, selectedModule]);

  const activeFile = selectedFile ?? hoveredFile;

  useEffect(() => {
    let alive = true;
    getUiConfigV1()
      .then((cfg) => {
        if (!alive) return;
        setUiConfig({
          schemaVersion: cfg.schemaVersion,
          graph: {
            edgeTypes: cfg.relationTypes.map((r) => ({
              id: r.id, label: r.label, defaultEnabled: r.defaultVisible,
            })),
            lineCategories: cfg.lineCategories.map((c) => ({
              id: c.id, label: c.label, defaultEnabled: c.defaultVisible,
            })),
            brightnessMetrics: cfg.metrics.map((m) => ({
              id: m.id, label: m.label, defaultEnabled: m.supportedViews.includes("graph"),
            })),
            nodeSizeMetrics: cfg.metrics.map((m) => ({
              id: m.id, label: m.label, defaultEnabled: m.supportedViews.includes("graph"),
            })),
            linkThicknessMetrics: cfg.metrics.map((m) => ({
              id: m.id, label: m.label, defaultEnabled: m.supportedViews.includes("graph"),
            })),
          },
        });
      })
      .catch(() => {
        if (alive) setUiConfig(null);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (uiConfig) {
      const defaults = uiConfig.graph.lineCategories.filter((o) => o.defaultEnabled).map((o) => o.id);
      setLineCategories(new Set(defaults));
    }
  }, [uiConfig]);

  useEffect(() => {
    if (uiConfig) {
      const defaults = uiConfig.graph.brightnessMetrics.filter((o) => o.defaultEnabled).map((o) => o.id);
      setBrightness(new Set(defaults));
    }
  }, [uiConfig]);

  useEffect(() => {
    setLoadingCommits(true);
    listCommitsV1()
      .then((rows) => {
        setCommits(rows);
        setSelectedCommit((current) => current ?? rows[rows.length - 1]?.commitId ?? null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoadingCommits(false));
  }, [setSelectedCommit]);

  useEffect(() => {
    if (!selectedCommit) {
      setFilesTable(null);
      return;
    }
    setSelectedFile(null);
    setHoveredFile(null);
    setFocusNotice(null);
    resetLayoutState();
    setError(null);
    getTableV1({ tableId: "entities.files", commitId: selectedCommit, parentEntityId: selectedModule ?? null })
      .then((proj) => {
        setFilesTable({ rows: proj.rows.map((r) => r.cells as Record<string, unknown>) });
      })
      .catch(() => setFilesTable(null));
  }, [resetLayoutState, selectedCommit, selectedModule]);

  useEffect(() => {
    if (!selectedCommit) {
      return;
    }
    const generation = graphGeneration.current + 1;
    graphGeneration.current = generation;
    setLoadingGraph(true);
    setError(null);
    getGraphV1({
      lensId: "module-dependencies",
      commitId: selectedCommit,
      includeZeroWeight: settings.filter.includeZeroScore,
    })
      .then((model) => {
        if (generation !== graphGeneration.current) {
          return;
        }
        setGraphModel(model);
        const selection = resolveGraphSelection(
          model.nodes.map((n) => ({
            module_name: n.entity.id,
            total_lines: 0,
            metrics: {},
            line_counts: n.lineCounts ?? {},
          })),
          focusModuleRef.current,
        );
        setSelectedModule(selection.selectedModule);
        if (selection.clearFocus) {
          setFilter({ focusEnabled: false, focusModule: null });
        }
        if (selection.notice) {
          setFocusNotice(selection.notice);
        }
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
  }, [focusModuleRef, selectedCommit, setFilter, settings.filter.includeZeroScore]);

  return (
    <Stack gap="md">
      <Title order={3}>{t("snapshot.title", "Report snapshot")}</Title>
      {error ? <Text c="red">{error}</Text> : null}
      {focusNotice ? (
        <Text size="sm" c="orange">
          {focusNotice}
        </Text>
      ) : null}
      <Group align="flex-end" wrap="wrap" gap="md">
        <Select
          label={t("common.commit", "Commit")}
          data={commitOptions}
          value={selectedCommit}
          onChange={setSelectedCommit}
          searchable
          w={420}
          disabled={loadingCommits || selectedCommitDisabled}
          rightSection={loadingCommits ? <Loader size="xs" /> : undefined}
        />
        <Text size="sm" c="dimmed" aria-label={t("common.commitDateUnavailable", "Date unavailable")}>
          {commitDateLabel
            ? t("snapshot.commitDate", "Commit date: {{date}}", { date: commitDateLabel })
            : t("common.commitDateUnavailable", "Date unavailable")}
        </Text>
        <Text size="sm" c="dimmed">
          {t("snapshot.visibleEdges", "Visible edges: {{count}}", {
            count: loadingGraph ? "…" : filterResult.stats.visibleEdges,
          })}
        </Text>
      </Group>
      <VisibleLinesSummary
        total={visibleCodeLines}
        selectedLabels={selectedCategoryLabels}
        loading={loadingGraph}
      />

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          {t("snapshot.graphView", "Graph view")}
        </Title>
        <Group align="flex-start" wrap="nowrap" gap="md" style={{ alignItems: "stretch" }}>
          <Stack gap="md" style={{ flex: 1, minWidth: "60%" }}>
            <ModuleGraph
              nodes={filterResult.nodes}
              edges={filterResult.edges}
              display={settings.display}
              force={settings.force}
              enabledEdgeKinds={settings.filter.enabledEdgeKinds}
              lineCategories={lineCategories}
              brightnessCriteria={brightness}
              selectedModule={selectedModule}
              onSelectModule={onSelectModule}
              pinned={graphPanelProps.pinned}
              onTogglePin={graphPanelProps.onTogglePin}
              layoutCommand={graphPanelProps.layoutCommand}
              onLayoutSnapshot={graphPanelProps.onLayoutSnapshot}
              zoomCommand={graphPanelProps.zoomCommand}
              loading={loadingGraph}
              emptyNotice={emptyNotice}
              initialLayout={graphPanelProps.initialLayout}
            />
          </Stack>
          <GraphSettingsPanel
            settings={settings}
            onFilterChange={graphPanelProps.setFilter}
            onDisplayChange={graphPanelProps.setDisplay}
            onForceChange={graphPanelProps.setForce}
            onSectionsExpandedChange={graphPanelProps.setSectionsExpanded}
            onResetForces={graphPanelProps.resetForces}
            onResetAll={graphPanelProps.onResetAll}
            onZoom={graphPanelProps.onZoom}
            onLayout={graphPanelProps.onLayout}
            onClearFocus={graphPanelProps.onClearFocus}
            onPinSelected={graphPanelProps.onPinSelected}
            edgeKindMeta={edgeKindMeta}
            maxEffectiveScore={maxEffectiveScore}
            selectedModule={selectedModule}
            commits={commits}
            selectedCommit={selectedCommit}
            commitPositionLabel={graphPanelProps.commitLabel}
            timelapse={graphPanelProps.timelapse}
            onTimelapse={graphPanelProps.onTimelapse}
            collapsed={graphPanelProps.panelCollapsed}
            onToggleCollapsed={graphPanelProps.onToggleCollapsed}
            saveNotice={graphPanelProps.panelSaveNotice}
            nodeSizeOptions={(uiConfig?.graph.nodeSizeMetrics ?? []).map((o) => ({
              id: o.id, label: o.label, unit: "", format: "",
              default_enabled: o.defaultEnabled, supported_levels: ["module", "file"],
            }))}
            linkThicknessOptions={(uiConfig?.graph.linkThicknessMetrics ?? []).map((o) => ({
              id: o.id, label: o.label, unit: "", format: "",
              default_enabled: o.defaultEnabled, supported_levels: ["module", "file"],
            }))}
            lineCategoryOptions={uiConfig?.graph.lineCategories.map((c) => ({
              id: c.id, label: c.label, default_enabled: c.defaultEnabled,
            }))}
            lineCategoryActive={lineCategories}
            onLineCategoryChange={setLineCategories}
            brightnessOptions={(uiConfig?.graph.brightnessMetrics ?? []).map((o) => ({
              id: o.id, label: o.label, unit: "", format: "",
              default_enabled: o.defaultEnabled, supported_levels: ["module", "file"],
            }))}
            brightnessActive={brightness}
            onBrightnessChange={setBrightness}
            edgeKindConfigLabels={edgeKindConfigLabels}
          />
        </Group>
      </Paper>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          {t("snapshot.moduleFileMap", "Module file map")}
        </Title>
        <Text size="sm" c="dimmed" mb="md">
          {t("snapshot.treemapHelp", "Treemap of files inside the selected module. Tile area is proportional to line count.")}
        </Text>
        <Text size="sm" mb="sm" c={selectedModule ? undefined : "dimmed"}>
          {selectedModule
            ? t("snapshot.moduleVisibleLines", "Module {{module}}: {{lines}} visible lines", {
                module: selectedModule,
                lines: formatCodeLines(moduleVisibleLines),
              })
            : t("snapshot.empty.selectModule", "Click a module on the graph to see its file map.")}
        </Text>
        {selectedModule ? (
          loadingGraph ? (
            <LoadingPanel label={t("snapshot.loading.moduleFiles", "Loading module files...")} />
          ) : (
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
          )
        ) : (
          <FileDetailPanel file={null} />
        )}
      </Paper>
    </Stack>
  );
}
