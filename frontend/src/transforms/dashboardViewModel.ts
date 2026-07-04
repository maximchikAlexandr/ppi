/**
 * Dashboard view-model derivation pipeline.
 *
 * Pure typed stages: normalize snapshot -> compute metrics -> build
 * aggregates -> build table rows -> build treemap nodes -> build
 * timelapse series -> format metrics.
 *
 * No React dependencies — testable outside components.
 */

import type { AnalysisSnapshot, ModuleRow } from "../api/__fixtures__/analysisResponses";

/** Dashboard view model */
export interface DashboardViewModel {
  readonly summary: DashboardSummary;
  readonly tableRows: ReadonlyArray<TableRow>;
  readonly treemapNodes: ReadonlyArray<TreemapNode>;
  readonly timelapseSeries: ReadonlyArray<TimelapsePoint>;
}

export interface DashboardSummary {
  readonly totalModules: number;
  readonly totalLines: number;
  readonly totalEdges: number;
}

export interface TableRow {
  readonly moduleName: string;
  readonly lines: number;
  readonly cyclomaticMean: number;
}

export interface TreemapNode {
  readonly name: string;
  readonly value: number;
}

interface TimelapsePoint {
  readonly date: string;
  readonly value: number;
}

/**
 * Compute summary metrics from a snapshot.
 */
export function computeMetrics(
  snapshot: AnalysisSnapshot,
): DashboardSummary {
  return {
    totalModules: snapshot.modules.length,
    totalLines: snapshot.modules.reduce(
      (sum, m) => sum + m.total_lines,
      0,
    ),
    totalEdges: snapshot.edges.length,
  };
}

/**
 * Build table rows from module data.
 */
export function buildTableRows(
  modules: ReadonlyArray<ModuleRow>,
): ReadonlyArray<TableRow> {
  return modules.map((m) => ({
    moduleName: m.module_name,
    lines: m.total_lines,
    cyclomaticMean: m.metrics.cyclomatic_mean ?? 0,
  }));
}

/**
 * Build treemap nodes for the module size visualization.
 */
export function buildTreemapNodes(
  modules: ReadonlyArray<ModuleRow>,
): ReadonlyArray<TreemapNode> {
  return modules.map((m) => ({
    name: m.module_name,
    value: m.total_lines,
  }));
}

/**
 * Build a complete dashboard view model from a snapshot.
 */
export function buildDashboardViewModel(
  snapshot: AnalysisSnapshot,
): DashboardViewModel {
  const summary = computeMetrics(snapshot);
  return {
    summary,
    tableRows: buildTableRows(snapshot.modules),
    treemapNodes: buildTreemapNodes(snapshot.modules),
    timelapseSeries: [],
  };
}
