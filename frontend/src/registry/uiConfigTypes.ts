import type { MetricDefinition } from "../domain/metric";
import type {
  EntityKindDefinition,
  RelationTypeDefinition,
  CapabilityDefinition,
  PageDefinition,
  LineCategoryDefinition,
} from "../domain";
import type { GraphLensDefinition } from "../domain/graph";
import type { VisualEncodingDefinition } from "../domain/visualEncoding";
import type { TableDefinition } from "../domain/table";
import type { QueryDefinition } from "../domain/query";

export type ProfileDefinition = {
  id: string;
  label: string;
  pluginIds: string[];
};

export type PluginContributionDefinition = {
  pluginId: string;
  label: string;
  contributes: {
    entityKinds: string[];
    metrics: string[];
    relationTypes: string[];
    tables: string[];
    graphLenses: string[];
    queries: string[];
    visualEncodings: string[];
  };
};

export type UiConfig = {
  schemaVersion: number;
  profile: ProfileDefinition;
  plugins: PluginContributionDefinition[];
  capabilities: CapabilityDefinition[];
  pages: PageDefinition[];
  entityKinds: EntityKindDefinition[];
  metrics: MetricDefinition[];
  relationTypes: RelationTypeDefinition[];
  lineCategories: LineCategoryDefinition[];
  visualEncodings: VisualEncodingDefinition[];
  graphLenses: GraphLensDefinition[];
  tables: TableDefinition[];
  queries: QueryDefinition[];
};
