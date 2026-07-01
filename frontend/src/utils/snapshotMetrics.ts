type NumericRecord = Readonly<Record<string, number>>;

function normalizeLineCategoryKey(categoryId: string): string {
  return categoryId === "test_lines" ? "python_test_lines" : categoryId;
}

export function lineCategoryValue(
  lineCounts: NumericRecord | undefined,
  categoryId: string,
): number {
  if (!lineCounts) return 0;
  return lineCounts[normalizeLineCategoryKey(categoryId)] ?? 0;
}

export function sumLineCounts(lineCounts: NumericRecord | undefined): number {
  if (!lineCounts) return 0;
  return Object.values(lineCounts).reduce((total, value) => total + value, 0);
}

export function resolveSnapshotMetricValue(args: {
  metricId: string;
  metrics?: NumericRecord;
  lineCounts?: NumericRecord;
  totalLines?: number;
}): number {
  const { metricId, metrics, lineCounts, totalLines } = args;
  switch (metricId) {
    case "cyclomatic":
      return metrics?.cyclomatic_median ?? 0;
    case "cognitive":
      return metrics?.cognitive_median ?? 0;
    case "jones":
      return metrics?.jones_median ?? 0;
    case "python_file_count":
      return metrics?.python_file_count ?? 0;
    case "lines":
    case "total_lines":
      return totalLines ?? lineCounts?.lines ?? 0;
    case "lines_by_category":
      return sumLineCounts(lineCounts);
    case "jones_line_count":
      return lineCounts?.jones_line_count ?? 0;
    case "function_count":
    case "method_count":
      return lineCounts?.function_count ?? metrics?.method_count ?? 0;
    default:
      return metrics?.[metricId] ?? 0;
  }
}
