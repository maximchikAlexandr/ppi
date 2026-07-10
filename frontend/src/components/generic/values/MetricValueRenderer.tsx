import type { MetricDefinition } from "../../../domain/metric";
import { NumberValueRenderer } from "./NumberValueRenderer";

type Props = {
  value: number | null | undefined;
  definition: MetricDefinition | null;
  fallbackLabel?: string;
};

export function MetricValueRenderer({ value, definition, fallbackLabel: label }: Props) {
  if (value === null || value === undefined) return <span>—</span>;
  const format = definition?.format ?? null;
  return (
    <span data-testid="metric-value" data-metric-id={definition?.id ?? label ?? "unknown"}>
      <NumberValueRenderer value={value} format={format} />
      {definition?.unit ? <small> {definition.unit}</small> : null}
    </span>
  );
}
