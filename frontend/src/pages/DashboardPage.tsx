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
import { useEffect, useMemo, useRef, useState } from "react";

import {
  listEntitiesV1,
  getMetricTimeseriesV1,
  getMetricHotspotsV1,
} from "../api/publicApi";
import type {
  HotspotItem,
  MetricQueryResult,
  TimeseriesPoint,
} from "../domain/query";
import type { EntityKindId } from "../domain/ids";
import type { MetricQueryStateResult } from "../domain/query";
import {
  normalizeMetricQueryState,
  getValidMetricsForEntityKind,
  getValidAggregationsForMetric,
} from "../transforms/dashboardTransforms";
import { HotspotsTable } from "../components/HotspotsTable";
import { MetricChart } from "../components/MetricChart";
import { t } from "../i18n";
import { useUiConfig } from "../registry/UiConfigProvider";

export function DashboardPage() {
  const { config, registry } = useUiConfig();
  const entityKinds = config?.entityKinds ?? [];
  const metrics = config?.metrics ?? [];
  const firstKindId = entityKinds[0]?.id ?? "";
  const [entityKindId, setEntityKindId] = useState<string>(firstKindId);
  const [metricId, setMetricId] = useState<string | null>(null);
  const [agg, setAgg] = useState<string>("mean");
  const [targetId, setTargetId] = useState<string | null>(null);
  const [targets, setTargets] = useState<readonly { id: string; label: string }[]>([]);
  const [points, setPoints] = useState<readonly TimeseriesPoint[]>([]);
  const [valueHotspots, setValueHotspots] = useState<readonly HotspotItem[]>([]);
  const [growthHotspots, setGrowthHotspots] = useState<readonly HotspotItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [recalculatedAt, setRecalculatedAt] = useState<number | null>(null);
  const hotspotsGeneration = useRef(0);
  const seriesGeneration = useRef(0);

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

  useEffect(() => {
    if (!entityKindId) {
      setTargets([]);
      return;
    }
    let alive = true;
    listEntitiesV1({ entityKindId })
      .then((rows) => {
        if (!alive) return;
        setTargets(rows.map((r) => ({ id: r.id, label: r.label })));
        if (rows.length && !targetId) {
          setTargetId(rows[0]?.id ?? null);
        }
      })
      .catch(() => {
        if (alive) setTargets([]);
      });
    return () => {
      alive = false;
    };
  }, [entityKindId, targetId]);

  const queryStateResult: MetricQueryStateResult = useMemo(() => {
    const normalized = normalizeMetricQueryState({
      entityKindId: entityKindId as EntityKindId,
      targetId,
      metricId: metricId as never,
      aggregation: agg,
      metrics,
    });
    if (!normalized) {
      return { status: "unavailable", reason: "no valid metric for entity kind" };
    }
    return { status: "valid", state: normalized };
  }, [entityKindId, targetId, metricId, agg, metrics]);

  useEffect(() => {
    if (queryStateResult.status !== "valid") {
      setPoints([]);
      return;
    }
    const generation = seriesGeneration.current + 1;
    seriesGeneration.current = generation;
    setError(null);
    getMetricTimeseriesV1({
      entityKindId: queryStateResult.state.entityKindId,
      metricId: queryStateResult.state.metricId,
      aggregation: queryStateResult.state.aggregation,
      targetId: queryStateResult.state.targetId,
    })
      .then((res: MetricQueryResult) => {
        if (generation !== seriesGeneration.current) return;
        if (res.resultKind !== "timeseries") return;
        setPoints(res.result.series[0]?.points ?? []);
        setRecalculatedAt(Date.now());
      })
      .catch((err: Error) => {
        if (generation === seriesGeneration.current) {
          setError(err.message);
        }
      });
  }, [queryStateResult]);

  useEffect(() => {
    if (queryStateResult.status !== "valid") {
      setValueHotspots([]);
      setGrowthHotspots([]);
      return;
    }
    const generation = hotspotsGeneration.current + 1;
    hotspotsGeneration.current = generation;
    setError(null);
    Promise.all([
      getMetricHotspotsV1({
        entityKindId: queryStateResult.state.entityKindId,
        metricId: queryStateResult.state.metricId,
        aggregation: queryStateResult.state.aggregation,
        rankBy: "value",
        limit: 20,
      }),
      getMetricHotspotsV1({
        entityKindId: queryStateResult.state.entityKindId,
        metricId: queryStateResult.state.metricId,
        aggregation: queryStateResult.state.aggregation,
        rankBy: "growth",
        limit: 20,
      }),
    ])
      .then(([byValue, byGrowth]) => {
        if (generation !== hotspotsGeneration.current) return;
        if (byValue.resultKind !== "ranking") return;
        if (byGrowth.resultKind !== "ranking") return;
        setValueHotspots(byValue.result.items);
        setGrowthHotspots(byGrowth.result.items);
        setRecalculatedAt(Date.now());
      })
      .catch((err: Error) => {
        if (generation === hotspotsGeneration.current) {
          setError(err.message);
        }
      });
  }, [queryStateResult]);

  const targetDisabled = targets.length === 0;
  const aggregationLabel = aggOptions.find((a) => a.id === agg)?.label ?? agg;
  const metricLabel = registry?.metricLabel(metricId ?? "") ?? metricId ?? "";

  return (
    <Stack gap="lg">
      <Title order={3}>{t("dashboard.title", "Metrics dashboard")}</Title>
      {error ? <Alert color="red">{error}</Alert> : null}
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
          data={targets.map((t) => ({ value: t.id, label: t.label }))}
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
          {t("common.unavailable", "Unavailable")}
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