import { Group, Loader, Paper, Select, Stack, Text, Title } from "@mantine/core";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  listCommitsV1,
  listTablesV1,
  getTableV1,
  type CommitSummaryV1,
} from "../api/publicApi";
import { t } from "../i18n";
import { useAppNavigation } from "../navigation";
import { toCommitSelectOptions } from "../transforms/commitOptions";
import { LoadingPanel } from "../components/LoadingPanel";
import { GenericDataTable } from "../components/generic/table/GenericDataTable";
import type { ActionDefinition } from "../domain/action";
import type { TableProjection } from "../domain/table";

export function TablesPage() {
  const { selectedCommit, setSelectedCommit } = useAppNavigation();
  const [commits, setCommits] = useState<readonly CommitSummaryV1[]>([]);
  const [tableDefs, setTableDefs] = useState<readonly { id: string; label: string }[]>([]);
  const [modulesProjection, setModulesProjection] = useState<TableProjection | null>(null);
  const [filesProjection, setFilesProjection] = useState<TableProjection | null>(null);
  const [relationsProjection, setRelationsProjection] = useState<TableProjection | null>(null);
  const [loadingCommits, setLoadingCommits] = useState(true);
  const [loadingSnapshot, setLoadingSnapshot] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const modulesGeneration = useRef(0);
  const relationsGeneration = useRef(0);
  const filesGeneration = useRef(0);

  const commitOptions = useMemo(() => toCommitSelectOptions(commits), [commits]);

  useEffect(() => {
    let alive = true;
    listTablesV1()
      .then((list) => {
        if (alive) setTableDefs(list.map((tbl) => ({ id: tbl.id, label: tbl.label })));
      })
      .catch(() => {
        if (alive) setTableDefs([]);
      });
    return () => {
      alive = false;
    };
  }, []);

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

  const modulesTableId = tableDefs.find((t) => t.id === "entities.modules")?.id ?? "entities.modules";
  const filesTableId = tableDefs.find((t) => t.id === "entities.files")?.id ?? "entities.files";
  const relationsTableId = tableDefs.find((t) => t.id === "relations.current")?.id ?? "relations.current";

  useEffect(() => {
    if (!selectedCommit) return;
    const generation = modulesGeneration.current + 1;
    modulesGeneration.current = generation;
    const relationsGen = relationsGeneration.current + 1;
    relationsGeneration.current = relationsGen;
    setModulesProjection(null);
    setRelationsProjection(null);
    setSelectedModule(null);
    setLoadingSnapshot(true);
    setError(null);
    Promise.all([
      getTableV1({ tableId: modulesTableId, commitId: selectedCommit }),
      getTableV1({ tableId: relationsTableId, commitId: selectedCommit }),
    ])
      .then(([modules, relations]) => {
        if (generation === modulesGeneration.current) setModulesProjection(modules);
        if (relationsGen === relationsGeneration.current) setRelationsProjection(relations);
      })
      .catch((err: Error) => {
        if (generation === modulesGeneration.current) setError(err.message);
      })
      .finally(() => {
        if (generation === modulesGeneration.current) setLoadingSnapshot(false);
      });
  }, [selectedCommit, modulesTableId, relationsTableId]);

  useEffect(() => {
    if (!selectedCommit || !selectedModule) {
      setFilesProjection(null);
      return;
    }
    const generation = filesGeneration.current + 1;
    filesGeneration.current = generation;
    getTableV1({ tableId: filesTableId, commitId: selectedCommit, parentEntityId: selectedModule })
      .then((proj) => {
        if (generation === filesGeneration.current) setFilesProjection(proj);
      })
      .catch((err: Error) => {
        if (generation === filesGeneration.current) setError(err.message);
      });
  }, [selectedCommit, selectedModule, filesTableId]);

  const handleModulesAction = (a: ActionDefinition) => {
    if (a.kind === "drilldown" && a.targetTableId) {
      const moduleName = String(a.params?.parentEntityId ?? selectedModule ?? "");
      setSelectedModule(moduleName);
    }
  };

  return (
    <Stack gap="md">
      <Title order={3}>{t("tables.title", "Tables")}</Title>
      {error ? <Text c="red">{error}</Text> : null}
      <Group align="flex-end" wrap="wrap">
        <Select
          label={t("common.commit", "Commit")}
          data={commitOptions}
          value={selectedCommit}
          onChange={setSelectedCommit}
          searchable
          w={420}
          disabled={loadingCommits}
          rightSection={loadingCommits ? <Loader size="xs" /> : undefined}
        />
      </Group>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          {t("tables.moduleLines.dynamic", "Module line counts")}
        </Title>
        {loadingSnapshot ? (
          <LoadingPanel label={t("snapshot.loading.moduleLines", "Loading module lines...")} />
        ) : modulesProjection ? (
          <GenericDataTable projection={modulesProjection} onAction={handleModulesAction} />
        ) : null}
      </Paper>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          {selectedModule
            ? t("tables.drilldown.files", "Files in {{module}}", { module: selectedModule })
            : t("snapshot.moduleFileMap", "Module file map")}
        </Title>
        {selectedModule ? (
          filesProjection ? (
            <GenericDataTable projection={filesProjection} />
          ) : (
            <LoadingPanel label={t("snapshot.loading.moduleFiles", "Loading module files...")} />
          )
        ) : (
          <Text size="sm" c="dimmed">
            {t("tables.noFile", "Pick a module to inspect its files.")}
          </Text>
        )}
      </Paper>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          {t("tables.relations.title", "Relations")}
        </Title>
        {loadingSnapshot ? (
          <LoadingPanel label={t("snapshot.loading.relations", "Loading relations...")} />
        ) : relationsProjection ? (
          <GenericDataTable projection={relationsProjection} />
        ) : (
          <Text c="dimmed">{t("tables.empty.relations", "No relations at this commit.")}</Text>
        )}
      </Paper>
    </Stack>
  );
}