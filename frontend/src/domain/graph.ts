import type { EntityRef } from "./entity";
import type { RelationTypeId, GraphLensId } from "./ids";
import type { MetricValue, MetricDistribution } from "./metric";
import type { RelationContribution } from "./relation";

export type EntityGraphNode = {
  entity: EntityRef;
  metrics: MetricValue[];
  distributions?: MetricDistribution[];
  attributes?: Record<string, unknown>;
  lineCounts?: Record<string, number>;
};

export type EntityGraphEdge = {
  id: string;
  source: EntityRef;
  target: EntityRef;
  relationTypeId: RelationTypeId;
  metrics: MetricValue[];
  contributions?: RelationContribution[];
  attributes?: Record<string, unknown>;
};

export type EntityGraphModel = {
  commitId: string;
  lensId: GraphLensId;
  nodes: EntityGraphNode[];
  edges: EntityGraphEdge[];
};

export type GraphLensDefinition = {
  id: GraphLensId;
  label: string;
  description?: string | null;
  nodeKinds: string[];
  relationTypes: RelationTypeId[];
  defaultVisualEncoding: GraphVisualEncodingConfig;
};

export type GraphVisualEncodingConfig = {
  nodeSizeEncodingId?: string | null;
  nodeColorEncodingId?: string | null;
  edgeThicknessEncodingId?: string | null;
  nodeBadgeEncodingIds?: string[];
};
