type Props = { value: string };

export function DateValueRenderer({ value }: Props) {
  if (!value) return <span>—</span>;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return <span>{value}</span>;
  return <span data-testid="date-iso">{d.toLocaleString()}</span>;
}
