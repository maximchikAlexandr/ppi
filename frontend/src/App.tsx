import { useCallback } from "react";
import { AppShell, Container, Group, Tabs, Text, Title } from "@mantine/core";

import { AppTab, NavigationProvider, useAppNavigation } from "./navigation";
import { DashboardPage } from "./pages/DashboardPage";
import { SnapshotPage } from "./pages/SnapshotPage";
import { TablesPage } from "./pages/TablesPage";
import { t } from "./i18n";
import { UiConfigProvider } from "./registry/UiConfigProvider";
import { getUiConfigV1 } from "./api/publicApi";

function AppTabs() {
  const { activeTab, setActiveTab } = useAppNavigation();

  return (
    <Tabs
      className="ppi-tabs"
      value={activeTab}
      onChange={(value) => setActiveTab((value ?? "snapshot") as AppTab)}
    >
      <Tabs.List mb="md">
        <Tabs.Tab value="snapshot">{t("tabs.report", "Report")}</Tabs.Tab>
        <Tabs.Tab value="dashboard">{t("tabs.dashboard", "Dashboard")}</Tabs.Tab>
        <Tabs.Tab value="tables">{t("tabs.tables", "Tables")}</Tabs.Tab>
      </Tabs.List>
      <Tabs.Panel value="snapshot" keepMounted={false}>
        <SnapshotPage />
      </Tabs.Panel>
      <Tabs.Panel value="dashboard" keepMounted={false}>
        <DashboardPage />
      </Tabs.Panel>
      <Tabs.Panel value="tables" keepMounted={false}>
        <TablesPage />
      </Tabs.Panel>
    </Tabs>
  );
}

export function App() {
  const loadUiConfig = useCallback(() => getUiConfigV1(), []);
  return (
    <NavigationProvider>
      <UiConfigProvider loader={loadUiConfig}>
        <AppShell header={{ height: 68 }} padding="md">
          <AppShell.Header className="ppi-header" px="md">
            <Group h="100%" gap="sm">
              <div className="ppi-brand-mark" aria-hidden="true">P</div>
              <div>
                <Title order={3} size="h4" c="white">Python Project Inspector</Title>
                <Text size="xs" c="rgba(255,255,255,.66)">Architecture intelligence</Text>
              </div>
            </Group>
          </AppShell.Header>
          <AppShell.Main>
            <Container size="xl" py="md">
              <AppTabs />
            </Container>
          </AppShell.Main>
        </AppShell>
      </UiConfigProvider>
    </NavigationProvider>
  );
}
