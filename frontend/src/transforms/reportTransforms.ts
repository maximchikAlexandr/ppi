import { filter, map, pipe, sortBy } from "remeda";

import type { EdgePointsResponse, EvidenceRow } from "../api/client";
import { isScoringEdgeKind } from "../registry/odooProfile";

export type KindRow = {
  source: string;
  target: string;
  kind: string;
  points: number;
  total: number;
  evidence: EvidenceRow[];
};

export function buildKindRows(payload: EdgePointsResponse): readonly KindRow[] {
  return pipe(
    filter(Object.entries(payload.kinds ?? {}), ([kind, points]) => isScoringEdgeKind(kind) && points > 0),
    map(([kind, points]) => ({
      source: payload.source,
      target: payload.target,
      kind,
      points,
      total: payload.breakdown.total,
      evidence: (payload.evidence ?? []).filter((item) => item.kind === kind),
    })),
    sortBy([(row) => -row.points, "desc"], [(row) => row.kind, "asc"]),
  );
}
