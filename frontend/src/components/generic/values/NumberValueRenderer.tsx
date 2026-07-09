type NumberFormat = { kind?: string; precision?: number | null } | null;

type Props = { value: number; format?: NumberFormat };

export function NumberValueRenderer({ value, format }: Props) {
  const kind = format?.kind ?? "decimal";
  const precision = format?.precision ?? undefined;
  if (kind === "integer") {
    return <span data-testid="number-integer">{Math.round(value).toLocaleString()}</span>;
  }
  if (kind === "compact") {
    return <span data-testid="number-compact">{new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value)}</span>;
  }
  if (kind === "percent") {
    return <span data-testid="number-percent">{`${(value * 100).toFixed(precision ?? 2)}%`}</span>;
  }
  return (
    <span data-testid="number-decimal">
      {value.toLocaleString(undefined, {
        minimumFractionDigits: precision,
        maximumFractionDigits: precision,
      })}
    </span>
  );
}
