import { Group, Loader, Paper, Select, Stack, Text, Title } from "@mantine/core";
import { useEffect, useMemo } from "react";

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
import { useDrilldownStack } from "../components/generic/table/useDrilldownStack";
import type { ActionDefinition } from "../domain/action";
import type { TableProjection } from "../domain/table";
import { isSuccess } from "../utils/remoteData";
import { useLatestRequest } from "../utils/useLatestRequest";

type TableRef = { id: string; label: string };

export function TablesPage() {
  const { selectedCommit, setSelectedCommit } = useAppNavigation();
  const commits = useLatestRequest<readonly CommitSummaryV1[]>();
  const tableDefs = useLatestRequest<readonly TableRef[]>();
  const modulesProjection = useLatestRequest<TableProjection>();
  const relationsProjection = useLatestRequest<TableProjection>();
  const filesProjection = useLatestRequest<TableProjection>();
  const drilldown = useDrilldownStack();

  useEffect(() => {
    tableDefs.run(listTablesV1().then((list) => list.map((tbl) => ({ id: tbl.id, label: tbl.label }))));
  }, []);

  useEffect(() => {
    commits.run(
      listCommitsV1().then((rows) => {
        setSelectedCommit((current) => current ?? rows[rows.length - 1]?.commitId ?? null);
        return rows;
      }),
    );
  }, [setSelectedCommit]);

  const defsList: readonly TableRef[] = isSuccess(tableDefs.state) ? tableDefs.state.data : [];
  const modulesTableId =
    defsList.find((t) => t.id === "entities.modules")?.id ?? "entities.modules";
  const filesTableId = defsList.find((t) => t.id === "entities.files")?.id ?? "entities.files";
  const relationsTableId =
    defsList.find((t) => t.id === "relations.current")?.id ?? "relations.current";

  useEffect(() => {
    if (!selectedCommit) {
      modulesProjection.reset();
      relationsProjection.reset();
      drilldown.clear();
      return;
    }
    modulesProjection.run(
      getTableV1({ tableId: modulesTableId, commitId: selectedCommit }),
    );
    relationsProjection.run(
      getTableV1({ tableId: relationsTableId, commitId: selectedCommit }),
    );
    drilldown.clear();
  }, [selectedCommit, modulesTableId, relationsTableId]);

  useEffect(() => {
    if (!selectedCommit || !drilldown.top) {
      filesProjection.reset();
      return;
    }
    const frame = drilldown.top;
    filesProjection.run(
      getTableV1({
        tableId: frame.tableId,
        commitId: selectedCommit,
        parentEntityId: (frame.params.parentEntityId as string | null) ?? null,
      }),
    );
  }, [selectedCommit, drilldown.top, filesTableId]);

  const commitList = isSuccess(commits.state) ? commits.state.data : [];
  const commitOptions = useMemo(() => toCommitSelectOptions(commitList), [commitList]);
  const modulesData = isSuccess(modulesProjection.state) ? modulesProjection.state.data : null;
  const relationsData = isSuccess(relationsProjection.state) ? relationsProjection.state.data : null;
  const filesData = isSuccess(filesProjection.state) ? filesProjection.state.data : null;
  const errorMessage =
    (modulesProjection.state.status === "error"
      ? `${modulesTableId}: ${String(modulesProjection.state.error)}`
      : relationsProjection.state.status === "error"
        ? `${relationsTableId}: ${String(relationsProjection.state.error)}`
        : filesProjection.state.status === "error"
          ? `${filesTableId}: ${String(filesProjection.state.error)}`
          : null);
  const loadingSnapshot =
    modulesProjection.state.status === "loading" ||
    relationsProjection.state.status === "loading";

  const handleModulesAction = (a: ActionDefinition) => {
    if (a.kind === "drilldown" && a.targetTableId) {
      drilldown.push({
        tableId: a.targetTableId,
        title: a.label,
        params: { ...a.params },
      });
    }
  };

  const topFrame = drilldown.top;
  const drilldownTitle = topFrame ? topFrame.title : t("snapshot.moduleFileMap", "Module file map");

  return (
    <Stack gap="md">
      <Title order={3}>{t("tables.title", "Tables")}</Title>
      {errorMessage ? (
        <Text c="red" size="sm" data-testid="tables-error">
          {t("tables.error", "Failed to load: {{error}}", { error: errorMessage })}
        </Text>
      ) : null}
      <Group align="flex-end" wrap="wrap">
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
        {drilldown.stack.length > 0 ? (
          <Text
            size="sm"
            c="blue"
            style={{ cursor: "pointer", alignSelf: "flex-end" }}
            onClick={() => drilldown.pop()}
            data-testid="drilldown-back"
          >
            {t("tables.drilldown.back", "Back")}
          </Text>
        ) : null}
      </Group>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          {t("tables.moduleLines.dynamic", "Module line counts")}
        </Title>
        {loadingSnapshot && !modulesData ? (
          <LoadingPanel label={t("snapshot.loading.moduleLines", "Loading module lines...")} />
        ) : modulesData ? (
          <GenericDataTable projection={modulesData} onAction={handleModulesAction} />
        ) : null}
      </Paper>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="xs">
          {drilldownTitle}
        </Title>
        {topFrame ? (
          filesData ? (
            <GenericDataTable projection={filesData} />
          ) : (
            <LoadingPanel label={t("snapshot.loading.moduleFiles", "Loading files...")} />
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
        {loadingSnapshot && !relationsData ? (
          <LoadingPanel label={t("snapshot.loading.relations", "Loading relations...")} />
        ) : relationsData ? (
          <GenericDataTable projection={relationsData} />
        ) : (
          <Text c="dimmed">{t("tables.empty.relations", "No relations at this commit.")}</Text>
        )}
      </Paper>
    </Stack>
  );
}
