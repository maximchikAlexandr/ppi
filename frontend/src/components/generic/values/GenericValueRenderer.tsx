/**
 * GenericValueRenderer: routes a value to the appropriate sub-renderer
 * based on metadata. Unknown value types render an escaped string.
 */
import { useUiConfig } from "../../../registry/UiConfigProvider";
import { fallbackLabel } from "../../../registry/fallbackLabels";
import { NumberValueRenderer } from "./NumberValueRenderer";
import { DateValueRenderer } from "./DateValueRenderer";
import { BooleanValueRenderer } from "./BooleanValueRenderer";
import { MetricValueRenderer } from "./MetricValueRenderer";

type ValueType = "string" | "number" | "integer" | "boolean" | "date" | "datetime" | "metric" | "entity" | "json";

type Props = {
  value: unknown;
  valueType?: ValueType;
  metricId?: string | null;
  format?: { kind: string; precision?: number | null } | null;
  fallbackLabel?: string | null;
};

export function GenericValueRenderer({
  value,
  valueType,
  metricId,
  format,
  fallbackLabel: fallback,
}: Props) {
  const ctx = useUiConfig();
  const registry = ctx.registry;

  if (value === null || value === undefined) {
    return <span data-testid="generic-value-null">—</span>;
  }

  if (valueType === "metric" && metricId && registry) {
    const def = registry.getMetric(metricId);
    return (
      <MetricValueRenderer
        value={value as number}
        definition={def}
        fallbackLabel={fallback ?? fallbackLabel(metricId)}
      />
    );
  }

  if (valueType === "number" || valueType === "integer") {
    return <NumberValueRenderer value={Number(value)} format={format} />;
  }

  if (valueType === "date" || valueType === "datetime") {
    return <DateValueRenderer value={String(value)} />;
  }

  if (valueType === "boolean") {
    return <BooleanValueRenderer value={Boolean(value)} />;
  }

  if (typeof value === "boolean") {
    return <BooleanValueRenderer value={value} />;
  }
  if (typeof value === "number") {
    return <NumberValueRenderer value={value} format={format} />;
  }

  return (
    <span data-testid="generic-value-string" data-value-type="unknown">
      {escapeText(String(value))}
    </span>
  );
}

function escapeText(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
