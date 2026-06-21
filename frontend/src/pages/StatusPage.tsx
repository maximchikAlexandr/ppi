import { Anchor, Alert, Badge, Group, Paper, SimpleGrid, Stack, Table, Text, Title } from "@mantine/core";
import { useEffect, useRef, useState } from "react";

import { fetchStatus, type RunFailureRow, type StatusResponse } from "../api/client";
import { useAppNavigation } from "../navigation";

export function StatusPage() {
  const { openSnapshot } = useAppNavigation();
  const failuresRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus()
      .then(setStatus)
      .catch((err: Error) => setError(err.message));
  }, []);

  function scrollToFailures() {
    failuresRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  if (error) {
    return <Alert color="red" title="Failed to load status">{error}</Alert>;
  }

  if (!status) {
    return <Text>Loading status…</Text>;
  }

  const runFailures = status.run_failures ?? [];

  return (
    <Stack gap="md">
      <Title order={3}>Analysis status</Title>
      <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
        <Paper withBorder p="md">
          <Text size="sm" c="dimmed">
            Project
          </Text>
          <Text fw={600}>{status.project_id ?? "—"}</Text>
        </Paper>
        <Paper withBorder p="md">
          <Text size="sm" c="dimmed">
            Branch
          </Text>
          <Text fw={600}>{status.branch ?? "—"}</Text>
        </Paper>
        <Paper withBorder p="md">
          <Text size="sm" c="dimmed">
            Schema version
          </Text>
          <Text fw={600}>{status.schema_version}</Text>
          <Text size="xs" c="dimmed">
            Expected: {status.expected_schema_version}
          </Text>
          {!status.schema_compatible ? (
            <Badge color="red" mt="xs">
              Incompatible — re-run analyze with --rebuild
            </Badge>
          ) : null}
        </Paper>
        <Paper withBorder p="md">
          <Text size="sm" c="dimmed">
            Commits stored
          </Text>
          <Text fw={600}>{status.commit_count}</Text>
        </Paper>
        <Paper withBorder p="md">
          <Text size="sm" c="dimmed">
            Store
          </Text>
          <Badge color={status.store_present ? "green" : "gray"}>
            {status.store_present ? "present" : "missing"}
          </Badge>
        </Paper>
        <Paper withBorder p="md">
          <Text size="sm" c="dimmed">
            Writer
          </Text>
          <Badge color={status.writer_active ? "yellow" : "green"}>
            {status.writer_active ? "active" : "idle"}
          </Badge>
        </Paper>
      </SimpleGrid>
      {status.scope ? (
        <Paper withBorder p="md">
          <Title order={4} mb="sm">
            Analysis scope
          </Title>
          <Stack gap={4}>
            <Text size="sm">Project label: {status.scope.project_label || "—"}</Text>
            <Text size="sm">Repo path: {status.scope.repo_path || "—"}</Text>
            <Text size="sm">All modules: {status.scope.all_modules ? "yes" : "no"}</Text>
            <Text size="sm">
              Module prefixes: {status.scope.module_prefixes.length ? status.scope.module_prefixes.join(", ") : "—"}
            </Text>
            <Text size="sm">
              Include modules: {status.scope.include_modules.length ? status.scope.include_modules.join(", ") : "—"}
            </Text>
          </Stack>
        </Paper>
      ) : null}
      {status.last_run ? (
        <Paper withBorder p="md">
          <Title order={4} mb="sm">
            Last run
          </Title>
          <Group gap="lg">
            <Text size="sm">Mode: {status.last_run.mode}</Text>
            <Text size="sm">Status: {status.last_run.status}</Text>
            <Text size="sm">
              Commits: {status.last_run.commits_succeeded}/{status.last_run.commits_total}
            </Text>
            {status.last_run.commits_failed ? (
              <Anchor component="button" type="button" onClick={scrollToFailures}>
                <Badge color="red" variant="light" style={{ cursor: "pointer" }}>
                  Failed: {status.last_run.commits_failed}
                </Badge>
              </Anchor>
            ) : null}
          </Group>
          {runFailures.length > 0 ? (
            <Stack gap="sm" mt="md" ref={failuresRef}>
              <Text size="sm" fw={600}>
                Failed commits and files
              </Text>
              <Table striped withTableBorder>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Commit</Table.Th>
                    <Table.Th>File</Table.Th>
                    <Table.Th>Error</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {runFailures.map((row: RunFailureRow, index) => (
                    <Table.Tr key={`${row.commit_hash}-${row.file_path}-${index}`}>
                      <Table.Td>
                        {row.commit_hash ? (
                          <Anchor
                            component="button"
                            type="button"
                            size="sm"
                            onClick={() => openSnapshot(row.commit_hash!, "failures")}
                          >
                            {row.commit_order != null ? `#${row.commit_order} ` : ""}
                            {row.commit_hash.slice(0, 8)}
                            {row.commit_summary ? ` ${row.commit_summary}` : ""}
                          </Anchor>
                        ) : (
                          "—"
                        )}
                      </Table.Td>
                      <Table.Td>{row.file_path ?? "—"}</Table.Td>
                      <Table.Td>{row.error_text}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Stack>
          ) : status.last_run.commits_failed ? (
            <Text size="sm" c="dimmed" mt="md" ref={failuresRef}>
              Failure details are not stored for this run. Re-run analyze to capture them.
            </Text>
          ) : null}
        </Paper>
      ) : (
        <Text c="dimmed">No analysis runs recorded yet.</Text>
      )}
    </Stack>
  );
}
