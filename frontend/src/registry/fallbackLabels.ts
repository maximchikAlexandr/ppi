/**
 * Deterministic fallback label conversion. Pure and idempotent.
 */
export function fallbackLabel(identifier: string | null | undefined): string {
  if (identifier === null || identifier === undefined) {
    return "—";
  }
  const raw = String(identifier).trim();
  if (raw === "") {
    return "—";
  }
  const hasAlnum = /[A-Za-z0-9]/.test(raw);
  if (!hasAlnum) {
    return "—";
  }
  const tokens = raw
    .split(/[\s._\-\/]+/u)
    .filter((t) => t.length > 0);
  if (tokens.length === 0) {
    return raw;
  }
  const titleCased = tokens
    .map((t) => t.charAt(0).toUpperCase() + t.slice(1).toLowerCase())
    .join(" ");
  return titleCased;
}
