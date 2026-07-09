/**
 * SnapshotPage: composes the generic EntityGraph, EntityTreemap and
 * TreemapItemDetailPanel. The page owns the selection state; no
 * legacy graph explorer or domain-shaped DTOs leak here.
 */
import { Group, Loader, Paper, Select, Stack, Text, Title } from "@mantine/core";
import { useEffect, useMemo, useState } from "react";

import {
  listCommitsV1,
  getUiConfigV1,
  getGraphV1,
  getTableV1,
  type CommitSummaryV1,
} from "../api/publicApi";
import { adaptTableToTreemap } from "../api/adapters/treemapAdapter";
import { EntityGraph } from "../components/generic/graph/EntityGraph";
import { GenericGraphSettingsBar } from "../components/generic/graph/GenericGraphSettingsBar";
import { EntityTreemap } from "../components/generic/treemap/EntityTreemap";
import { TreemapItemDetailPanel } from "../components/generic/treemap/TreemapItemDetailPanel";
import { t } from "../i18n";
import { useAppNavigation } from "../navigation";
import { toCommitSelectOptions } from "../transforms/commitOptions";
import { formatCommitDate } from "../transforms/commitDate";
import { LoadingPanel } from "../components/LoadingPanel";
import { isSuccess } from "../utils/remoteData";
import { useLatestRequest } from "../utils/useLatestRequest";
import type { EntityGraphModel } from "../domain/graph";
import type { EntityRef } from "../domain/entity";
import type { TableProjection } from "../domain/table";
import type { EntityKindId, EntityId } from "../domain/ids";
import type { TreemapItem, TreemapProjection } from "../domain/treemap";

type UiConfigState = {
  schemaVersion: number;
  lineCategories: readonly { id: string; label: string; defaultEnabled: boolean }[];
};

const TREEMAP_SIZE_COLUMN = "lines";
const FILE_ENTITY_KIND: EntityKindId = "file";

export function SnapshotPage() {
  const { selectedCommit, setSelectedCommit } = useAppNavigation();
  const commits = useLatestRequest<readonly CommitSummaryV1[]>();
  const graphModel = useLatestRequest<EntityGraphModel>();
  const filesTable = useLatestRequest<TableProjection>();
  const [uiConfig, setUiConfig] = useState<UiConfigState | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<EntityRef | null>(null);
  const [selectedFileId, setSelectedFileId] = useState<EntityId | null>(null);
  const [hoveredFileId, setHoveredFileId] = useState<EntityId | null>(null);
  const [lineCategories, setLineCategories] = useState<Set<string>>(new Set());

  useEffect(() => {
    let alive = true;
    getUiConfigV1()
      .then((cfg) => {
        if (!alive) return;
        setUiConfig({
          schemaVersion: cfg.schemaVersion,
          lineCategories: cfg.lineCategories.map((c) => ({
            id: c.id, label: c.label, defaultEnabled: c.defaultVisible,
          })),
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
      const defaults = uiConfig.lineCategories.filter((o) => o.defaultEnabled).map((o) => o.id);
      setLineCategories(new Set(defaults));
    }
  }, [uiConfig]);

  useEffect(() => {
    commits.run(listCommitsV1().then((rows) => {
      setSelectedCommit((current) => current ?? rows[rows.length - 1]?.commitId ?? null);
      return rows;
    }));
  }, [setSelectedCommit]);

  useEffect(() => {
    if (!selectedCommit) {
      graphModel.reset();
      return;
    }
    setSelectedFileId(null);
    setHoveredFileId(null);
    graphModel.run(
      getGraphV1({
        lensId: "module-dependencies",
        commitId: selectedCommit,
      }),
    );
  }, [selectedCommit]);

  useEffect(() => {
    if (!selectedCommit) {
      filesTable.reset();
      return;
    }
    filesTable.run(
      getTableV1({
        tableId: "entities.files",
        commitId: selectedCommit,
        parentEntityId: selectedEntity?.id ?? null,
      }),
    );
  }, [selectedCommit, selectedEntity?.id]);

  const commitList = isSuccess(commits.state) ? commits.state.data : [];
  const commitOptions = useMemo(() => toCommitSelectOptions(commitList), [commitList]);
  const model = isSuccess(graphModel.state) ? graphModel.state.data : null;
  const fileProjection = isSuccess(filesTable.state) ? filesTable.state.data : null;
  const treemap: TreemapProjection = useMemo(() => {
    if (!fileProjection) return { title: "Files", items: [] };
    return adaptTableToTreemap(fileProjection, {
      sizeColumnId: TREEMAP_SIZE_COLUMN,
      entityKindId: FILE_ENTITY_KIND,
    });
  }, [fileProjection]);

  // When the graph model arrives, pick the first visible node so the
  // treemap has a parent to drill into.
  useEffect(() => {
    if (!model) return;
    setSelectedEntity((current) => current ?? model.nodes[0]?.entity ?? null);
  }, [model]);

  // The drilldown contract: when a tile is selected, expose it as the
  // current entity so the files table re-fetches for that parent.
  const handleTileSelect = (itemId: EntityId) => {
    setSelectedFileId(itemId);
    if (model) {
      const node = model.nodes.find((n) => n.entity.id === itemId);
      if (node) setSelectedEntity(node.entity);
    }
  };

  const selectedTreemapItem: TreemapItem | null = useMemo(() => {
    if (!selectedFileId) return null;
    return treemap.items.find((i) => i.entity.id === selectedFileId) ?? null;
  }, [selectedFileId, treemap.items]);

  const hoveredTreemapItem: TreemapItem | null = useMemo(() => {
    if (!hoveredFileId) return null;
    return treemap.items.find((i) => i.entity.id === hoveredFileId) ?? null;
  }, [hoveredFileId, treemap.items]);

  return (
    <Stack gap="md">
      <Title order={3}>{t("snapshot.title", "Report snapshot")}</Title>
      <Group align="flex-end" wrap="wrap" gap="md">
        <Select
          label={t("common.commit", "Commit")}
          data={commitOptions}
          value={selectedCommit}
          onChange={setSelectedCommit}
          searchable
          w={420}
          disabled={commits.state.status === "loading"}
          rightSection={commits.state.status === "loading" ? <Loader size="xs" /> : undefined}
        />
        <Text size="sm" c="dimmed" aria-label={t("common.commitDateUnavailable", "Date unavailable")}>
          {(() => {
            const row = commitList.find((c) => c.commitId === selectedCommit) ?? null;
            const date = formatCommitDate(row?.authoredAt ?? null);
            return date
              ? t("snapshot.commitDate", "Commit date: {{date}}", { date })
              : t("common.commitDateUnavailable", "Date unavailable");
          })()}
        </Text>
      </Group>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          {t("snapshot.graphView", "Graph view")}
        </Title>
        <Group align="flex-start" wrap="nowrap" gap="md" style={{ alignItems: "stretch" }}>
          <Stack gap="md" style={{ flex: 1, minWidth: "60%" }}>
            {model ? (
              <EntityGraph
                model={model}
                onSelectNode={(id) => {
                  const node = model.nodes.find((n) => n.entity.id === id);
                  if (node) setSelectedEntity(node.entity);
                }}
              />
            ) : (
              <LoadingPanel label={t("snapshot.loading.graph", "Loading graph...")} />
            )}
          </Stack>
          <Stack style={{ width: 280 }}>
            <GenericGraphSettingsBar
              lineCategoryOptions={uiConfig?.lineCategories ?? []}
              activeLineCategories={lineCategories}
              onLineCategoryChange={setLineCategories}
              onClearFocus={() => setSelectedEntity(null)}
            />
          </Stack>
        </Group>
      </Paper>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          {t("snapshot.moduleFileMap", "Module file map")}
        </Title>
        <Text size="sm" c="dimmed" mb="md">
          {t(
            "snapshot.treemapHelp",
            "Treemap of files inside the selected module. Tile area is proportional to line count.",
          )}
        </Text>
        {selectedEntity ? (
          <Stack gap="md">
            <EntityTreemap
              projection={treemap}
              selectedId={selectedFileId}
              onSelect={handleTileSelect}
              onHover={setHoveredFileId}
            />
            <TreemapItemDetailPanel
              item={selectedTreemapItem ?? hoveredTreemapItem}
            />
          </Stack>
        ) : (
          <Text size="sm" c="dimmed">
            {t("snapshot.empty.selectModule", "Click a node on the graph to see its file map.")}
          </Text>
        )}
      </Paper>
    </Stack>
  );
}
