/**
 * Adapter: /api/v1/entities DTO -> generic EntityTarget[].
 */
import type { EntityTarget } from "../../domain/entity";

type Dto = {
  entityKindId?: string;
  commitId?: string | null;
  items?: {
    id?: string;
    kind?: string;
    label?: string;
    path?: string | null;
    pluginId?: string | null;
    selectable?: boolean;
    reason?: string | null;
  }[];
};

export function adaptEntities(dto: Dto): EntityTarget[] {
  return (dto.items ?? []).map((e) => ({
    id: e.id ?? "",
    kind: e.kind ?? dto.entityKindId ?? "unknown",
    label: e.label ?? e.id ?? "—",
    path: e.path ?? null,
    pluginId: e.pluginId ?? null,
    selectable: e.selectable ?? true,
    reason: e.reason ?? null,
  }));
}
