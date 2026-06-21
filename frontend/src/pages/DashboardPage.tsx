import { LineChart } from "@mantine/charts";
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
  fetchCatalog,
  fetchHotspots,
  fetchTimeseries,
  type HotspotItem,
  type TimeseriesPoint,
} from "../api/client";
import { HotspotsTable } from "../components/HotspotsTable";
import { MetricChart } from "../components/MetricChart";
import { CHART_CATEGORY_COLORS, LINE_CATEGORIES } from "../registry/odooProfile";

const COMPLEXITY_METRICS = [
  { value: "cyclomatic", label: "Cyclomatic" },
  { value: "cognitive", label: "Cognitive" },
  { value: "jones", label: "Jones" },
];

const MODULE_METRICS = [
  ...COMPLEXITY_METRICS,
  { value: "python_file_count", label: "Python file count" },
];

const AGGS = [
  { value: "mean", label: "Mean" },
  { value: "median", label: "Median" },
  { value: "p95", label: "P95" },
  { value: "max", label: "Max" },
];

export function DashboardPage() {
  const [level, setLevel] = useState<"module" | "file">("module");
  const [metric, setMetric] = useState("cyclomatic");
  const [agg, setAgg] = useState("mean");
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const [names, setNames] = useState<string[]>([]);
  const [complexityPoints, setComplexityPoints] = useState<TimeseriesPoint[]>([]);
  const [sizePoints, setSizePoints] = useState<TimeseriesPoint[]>([]);
  const [categoryChart, setCategoryChart] = useState<Record<string, number | string>[]>([]);
  const [categorySeries, setCategorySeries] = useState<{ name: string; label: string; color: string }[]>([]);
  const [valueHotspots, setValueHotspots] = useState<HotspotItem[]>([]);
  const [growthHotspots, setGrowthHotspots] = useState<HotspotItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const hotspotsGeneration = useRef(0);
  const seriesGeneration = useRef(0);

  const metricOptions = level === "module" ? MODULE_METRICS : COMPLEXITY_METRICS;
  const hotspotAgg = metric === "python_file_count" ? "mean" : agg;

  const nameOptions = useMemo(
    () => names.map((name) => ({ value: name, label: name })),
    [names],
  );

  useEffect(() => {
    fetchCatalog(level)
      .then((payload) => setNames(payload.names))
      .catch((err: Error) => setError(err.message));
  }, [level]);

  useEffect(() => {
    if (!names.length) {
      setSelectedName(null);
      return;
    }
    if (!selectedName || !names.includes(selectedName)) {
      setSelectedName(names[0]);
    }
  }, [names, selectedName]);

  useEffect(() => {
    if (level === "file" && metric === "python_file_count") {
      setMetric("cyclomatic");
    }
  }, [level, metric]);

  useEffect(() => {
    const generation = hotspotsGeneration.current + 1;
    hotspotsGeneration.current = generation;
    setError(null);
    Promise.all([
      fetchHotspots({ level, metric, by: "value", limit: 20, agg: hotspotAgg }),
      fetchHotspots({ level, metric, by: "growth", limit: 20, agg: hotspotAgg }),
    ])
      .then(([byValue, byGrowth]) => {
        if (generation !== hotspotsGeneration.current) {
          return;
        }
        setValueHotspots(byValue.items);
        setGrowthHotspots(byGrowth.items);
      })
      .catch((err: Error) => {
        if (generation === hotspotsGeneration.current) {
          setError(err.message);
        }
      });
  }, [hotspotAgg, level, metric]);

  useEffect(() => {
    if (!selectedName || !names.includes(selectedName)) {
      return;
    }
    const generation = seriesGeneration.current + 1;
    seriesGeneration.current = generation;
    setError(null);
    const requests = [
      fetchTimeseries({
        level,
        metric,
        name: selectedName,
        agg: metric === "python_file_count" ? undefined : agg,
      }),
      fetchTimeseries({ level, metric: "lines", name: selectedName }),
    ];
    if (level === "module") {
      requests.push(fetchTimeseries({ level: "module", metric: "lines_by_category", name: selectedName }));
    }
    Promise.all(requests)
      .then(([complexity, size, categories]) => {
        if (generation !== seriesGeneration.current) {
          return;
        }
        setComplexityPoints(complexity.series[0]?.points ?? []);
        setSizePoints(size.series[0]?.points ?? []);
        if (categories) {
          const orders = [
            ...new Set(categories.series.flatMap((series) => series.points.map((point) => point.commit_order))),
          ].sort((a, b) => a - b);
          setCategoryChart(
            orders.map((order) => {
              const row: Record<string, number | string> = { order };
              categories.series.forEach((series) => {
                const key = series.name.split("/").pop() ?? series.name;
                row[key] = Number(series.points.find((point) => point.commit_order === order)?.value ?? 0);
              });
              return row;
            }),
          );
          setCategorySeries(
            LINE_CATEGORIES.map(({ key, label }, index) => ({
              name: key,
              label,
              color: CHART_CATEGORY_COLORS[index % CHART_CATEGORY_COLORS.length],
            })),
          );
        } else {
          setCategoryChart([]);
          setCategorySeries([]);
        }
      })
      .catch((err: Error) => {
        if (generation === seriesGeneration.current) {
          setError(err.message);
        }
      });
  }, [agg, level, metric, names, selectedName]);

  return (
    <Stack gap="lg">
      <Title order={3}>Metrics dashboard</Title>
      {error ? <Alert color="red">{error}</Alert> : null}
      <Group align="flex-end" wrap="wrap">
        <Select
          label="Level"
          data={[
            { value: "module", label: "Module" },
            { value: "file", label: "File" },
          ]}
          value={level}
          onChange={(value) => setLevel((value as "module" | "file") ?? "module")}
          w={140}
        />
        <Select
          label="Target"
          data={nameOptions}
          value={selectedName}
          onChange={setSelectedName}
          searchable
          nothingFoundMessage="No targets"
          w={320}
        />
        <Select
          label="Metric"
          data={metricOptions}
          value={metric}
          onChange={(value) => setMetric(value ?? "cyclomatic")}
          w={180}
        />
        {metric !== "python_file_count" ? (
          <Select
            label="Aggregation"
            data={AGGS}
            value={agg}
            onChange={(value) => setAgg(value ?? "mean")}
            w={140}
          />
        ) : null}
      </Group>

      <Tabs defaultValue="complexity">
        <Tabs.List>
          <Tabs.Tab value="complexity">Complexity over time</Tabs.Tab>
          <Tabs.Tab value="size">Line count history</Tabs.Tab>
          {level === "module" ? <Tabs.Tab value="categories">Line categories</Tabs.Tab> : null}
          <Tabs.Tab value="hotspots">Hotspots</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="complexity" pt="md">
          <MetricChart
            title={`${metric}${metric === "python_file_count" ? "" : ` (${agg})`} — ${selectedName ?? ""}`}
            points={complexityPoints}
            yLabel={metric}
          />
        </Tabs.Panel>

        <Tabs.Panel value="size" pt="md">
          <MetricChart
            title={`Total lines — ${selectedName ?? ""}`}
            points={sizePoints}
            yLabel="lines"
          />
        </Tabs.Panel>

        {level === "module" ? (
          <Tabs.Panel value="categories" pt="md">
            {categoryChart.length ? (
              <LineChart h={280} data={categoryChart} dataKey="order" series={categorySeries} withLegend withTooltip />
            ) : (
              <Text c="dimmed">Select a module to load line category history.</Text>
            )}
          </Tabs.Panel>
        ) : null}

        <Tabs.Panel value="hotspots" pt="md">
          <SimpleGrid cols={{ base: 1, md: 2 }}>
            <HotspotsTable
              title={`Top by current ${metric}`}
              items={valueHotspots}
              showGrowth={false}
            />
            <HotspotsTable
              title={`Top by ${metric} growth`}
              items={growthHotspots}
              showGrowth
            />
          </SimpleGrid>
        </Tabs.Panel>
      </Tabs>

      {!selectedName ? (
        <Text c="dimmed">Run analysis and pick a target to load charts.</Text>
      ) : null}
    </Stack>
  );
}
