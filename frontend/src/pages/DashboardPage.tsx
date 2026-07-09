import {
  Alert,
  Group,
  Select,
  SimpleGrid,
  Stack,
  Tabs,
  Text,
  Title,
} from "@mantine/core";
import { useEffect, useMemo, useState } from "react";

import {
  listEntitiesV1,
  getMetricTimeseriesV1,
  getMetricHotspotsV1,
} from "../api/publicApi";
import type {
  HotspotItem,
  TimeseriesPoint,
  MetricQueryStateResult,
} from "../domain/query";
import type { EntityKindId } from "../domain/ids";
import { useUiConfig } from "../registry/UiConfigProvider";
import {
  normalizeMetricQueryState,
  getValidMetricsForEntityKind,
  getValidAggregationsForMetric,
  type MetricQueryUnavailableReason,
} from "../transforms/dashboardTransforms";
import { HotspotsTable } from "../components/HotspotsTable";
import { MetricChart } from "../components/MetricChart";
import { t } from "../i18n";
import { isSuccess, type RemoteData } from "../utils/remoteData";
import { useLatestRequest } from "../utils/useLatestRequest";

type EntityRefLite = { id: string; label: string };

export function DashboardPage() {
  const { config, registry } = useUiConfig();
  const entityKinds = config?.entityKinds ?? [];
  const metrics = config?.metrics ?? [];
  const firstKindId = entityKinds[0]?.id ?? "";
  const [entityKindId, setEntityKindId] = useState<string>(firstKindId);
  const [metricId, setMetricId] = useState<string | null>(null);
  const [agg, setAgg] = useState<string>("mean");
  const [targetId, setTargetId] = useState<string | null>(null);
  const [recalculatedAt, setRecalculatedAt] = useState<number | null>(null);

  useEffect(() => {
    if (firstKindId && entityKindId !== firstKindId && !entityKinds.some((k) => k.id === entityKindId)) {
      setEntityKindId(firstKindId);
    }
  }, [firstKindId, entityKindId, entityKinds]);

  const validMetrics = useMemo(
    () => getValidMetricsForEntityKind(metrics, entityKindId as EntityKindId),
    [metrics, entityKindId],
  );
  const metricDisabled = validMetrics.length === 0;

  const currentMetricDef = useMemo(
    () => validMetrics.find((m) => m.id === metricId) ?? null,
    [validMetrics, metricId],
  );
  const validAggregations = useMemo(
    () => getValidAggregationsForMetric(currentMetricDef),
    [currentMetricDef],
  );
  const aggOptions = useMemo(
    () => validAggregations.map((id, i) => ({ id, label: id, defaultEnabled: i === 0 })),
    [validAggregations],
  );

  const targets = useLatestRequest<readonly EntityRefLite[]>();
  useEffect(() => {
    if (!entityKindId) {
      targets.reset();
      return;
    }
    targets.run(
      listEntitiesV1({ entityKindId }).then((rows) =>
        rows.map((r) => ({ id: r.id, label: r.label })),
      ),
    );
  }, [entityKindId]);

  // Auto-select the first target when targets become available and no
  // selection is set. Mirrors the original `if (rows.length && !targetId)`
  // behaviour; lives in its own effect so the request effect stays
  // single-purpose.
  useEffect(() => {
    if (!isSuccess(targets.state)) return;
    if (targetId !== null) return;
    const first = targets.state.data[0];
    if (first) setTargetId(first.id);
  }, [targets.state, targetId]);

  const queryStateResult: MetricQueryStateResult = useMemo(
    () =>
      normalizeMetricQueryState({
        entityKindId: entityKindId ? (entityKindId as EntityKindId) : null,
        targetId,
        metricId: metricId ? (metricId as never) : null,
        aggregation: agg,
        metrics,
        availableTargetIds: new Set(
          isSuccess(targets.state) ? targets.state.data.map((t) => t.id) : [],
        ),
      }),
    [agg, entityKindId, metricId, metrics, targets.state],
  );

  const unavailableReason: MetricQueryUnavailableReason | null =
    queryStateResult.status === "unavailable" ? queryStateResult.reason : null;

  const series = useLatestRequest<readonly TimeseriesPoint[]>();
  const hotspots = useLatestRequest<{ value: readonly HotspotItem[]; growth: readonly HotspotItem[] }>();
  const queryError: RemoteData<never, string> | null =
    series.state.status === "error"
      ? series.state
      : hotspots.state.status === "error"
        ? hotspots.state
        : null;
  const errorMessage =
    queryError && queryError.status === "error" ? String(queryError.error) : null;

  useEffect(() => {
    if (queryStateResult.status !== "valid") {
      series.reset();
      hotspots.reset();
      return;
    }
    const { entityKindId: kind, metricId: mid, aggregation, targetId: tid } = queryStateResult.state;
    series.run(
      getMetricTimeseriesV1({
        entityKindId: kind,
        metricId: mid,
        aggregation,
        targetId: tid,
      }).then((res) =>
        res.resultKind === "timeseries" ? (res.result.series[0]?.points ?? []) : [],
      ),
    );
    hotspots.run(
      Promise.all([
        getMetricHotspotsV1({ entityKindId: kind, metricId: mid, aggregation, rankBy: "value", limit: 20 }),
        getMetricHotspotsV1({ entityKindId: kind, metricId: mid, aggregation, rankBy: "growth", limit: 20 }),
      ]).then(([byValue, byGrowth]) => ({
        value: byValue.resultKind === "ranking" ? byValue.result.items : [],
        growth: byGrowth.resultKind === "ranking" ? byGrowth.result.items : [],
      })),
    );
    setRecalculatedAt(Date.now());
  }, [queryStateResult]);

  const targetList: readonly EntityRefLite[] = isSuccess(targets.state) ? targets.state.data : [];
  const points: readonly TimeseriesPoint[] = isSuccess(series.state) ? series.state.data : [];
  const valueHotspots: readonly HotspotItem[] = isSuccess(hotspots.state) ? hotspots.state.data.value : [];
  const growthHotspots: readonly HotspotItem[] = isSuccess(hotspots.state) ? hotspots.state.data.growth : [];
  const targetDisabled = targetList.length === 0;
  const aggregationLabel = aggOptions.find((a) => a.id === agg)?.label ?? agg;
  const metricLabel = registry?.metricLabel(metricId ?? "") ?? metricId ?? "";
  const unavailableMessage = unavailableReason
    ? t(`dashboard.unavailable.${unavailableReason}`, t("common.unavailable", "Unavailable"))
    : null;

  return (
    <Stack gap="lg">
      <Title order={3}>{t("dashboard.title", "Metrics dashboard")}</Title>
      {errorMessage ? <Alert color="red">{errorMessage}</Alert> : null}
      <Group align="flex-end" wrap="wrap">
        <Select
          label={t("dashboard.level", "Entity kind")}
          data={entityKinds.map((k) => ({ value: k.id, label: k.label }))}
          value={entityKindId}
          onChange={(value) => setEntityKindId(value ?? "")}
          w={180}
        />
        <Select
          label={t("dashboard.target", "Target")}
          data={targetList.map((t) => ({ value: t.id, label: t.label }))}
          value={targetId}
          onChange={setTargetId}
          searchable
          nothingFoundMessage={
            targetDisabled
              ? t("common.unavailable", "Unavailable")
              : t("dashboard.noTargets", "No targets")
          }
          w={320}
          disabled={targetDisabled}
        />
        <Select
          label={t("dashboard.metric", "Metric")}
          data={validMetrics.map((m) => ({ value: m.id, label: m.label }))}
          value={metricId ?? ""}
          onChange={(value) => setMetricId(value ?? null)}
          w={180}
          disabled={metricDisabled}
          nothingFoundMessage={t("dashboard.noMetric", "No metric available")}
        />
        <Select
          label={t("dashboard.aggregation", "Aggregation")}
          data={aggOptions.map((a) => ({ value: a.id, label: a.label }))}
          value={agg}
          onChange={(value) => setAgg(value ?? "mean")}
          w={140}
        />
      </Group>

      {queryStateResult.status === "unavailable" ? (
        <Alert color="gray" variant="light" data-testid="dashboard-unavailable">
          {unavailableMessage}
        </Alert>
      ) : null}

      <Text size="sm" c="dimmed">
        {t("dashboard.aggregation.meta", "Aggregation: {{agg}}", { agg: aggregationLabel })}
        {recalculatedAt
          ? ` · ${t("dashboard.recalculated", "Recalculated for {{agg}}", { agg: aggregationLabel })}`
          : ""}
      </Text>

      <Tabs value="complexity" onChange={() => {}}>
        <Tabs.List>
          <Tabs.Tab value="complexity">{t("dashboard.tabs.complexity", "Metric over time")}</Tabs.Tab>
          <Tabs.Tab value="hotspots">{t("dashboard.tabs.hotspots", "Hotspots")}</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="complexity" pt="md">
          <MetricChart
            title={t("dashboard.chart.complexityTitle", "{{metric}} ({{agg}}) - {{name}}", {
              metric: metricLabel,
              agg: aggregationLabel,
              name: targetId ?? "",
            })}
            points={points}
            yLabel={metricLabel}
          />
        </Tabs.Panel>

        <Tabs.Panel value="hotspots" pt="md">
          <SimpleGrid cols={{ base: 1, md: 2 }}>
            <HotspotsTable
              title={t("dashboard.hotspots.current", "Top by current {{metric}}", { metric: metricLabel })}
              items={valueHotspots}
              showGrowth={false}
            />
            <HotspotsTable
              title={t("dashboard.hotspots.growth", "Top by {{metric}} growth", { metric: metricLabel })}
              items={growthHotspots}
              showGrowth
            />
          </SimpleGrid>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}