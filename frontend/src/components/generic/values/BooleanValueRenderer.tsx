type Props = { value: boolean };

const TRUE_LABELS = ["yes", "on", "true"];
const FALSE_LABELS = ["no", "off", "false"];
const EMPTY_LABEL = "—";

export function BooleanValueRenderer({ value }: Props) {
  if (value === true) return <span data-testid="boolean-true">{TRUE_LABELS[0]}</span>;
  if (value === false) return <span data-testid="boolean-false">{FALSE_LABELS[0]}</span>;
  return <span data-testid="boolean-empty">{EMPTY_LABEL}</span>;
}

export const BOOLEAN_LABELS = { TRUE: TRUE_LABELS, FALSE: FALSE_LABELS, EMPTY: EMPTY_LABEL };
