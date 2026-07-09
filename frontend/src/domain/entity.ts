import type { EntityId, EntityKindId } from "./ids";

export type EntityKindDefinition = {
  id: EntityKindId;
  label: string;
  pluralLabel: string;
  description?: string | null;
  icon?: string | null;
  defaultTableId?: string | null;
  supportedViews: string[];
};

export type EntityRef = {
  id: EntityId;
  kind: EntityKindId;
  label: string;
  path?: string | null;
  pluginId?: string | null;
};

export type EntityTarget = EntityRef & {
  selectable: boolean;
  reason?: string | null;
};
