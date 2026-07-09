# Contract: Public API v1

**Feature**: `010-frontend-api-platform`  
**Status**: Hardened draft; implementation not yet complete  
**Rule**: This contract is precise enough for implementation. Do not invent alternative endpoint names, field names, or response shapes.

## 1. Global Rules

- Base path: `/api/v1`.
- Public JSON field naming: `camelCase`.
- Internal Python fields may use `snake_case` only behind Pydantic aliases.
- All public operations MUST have stable `operationId`.
- All public operations MUST have tags.
- All public operations MUST document `ErrorResponse`.
- All public operations MUST return JSON.
- Public endpoints MUST NOT expose domain-shaped legacy DTOs.

## 2. Common Types

### ErrorResponse

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {},
    "requestId": "string"
  }
}
```

### EntityRef

```json
{
  "id": "string",
  "kind": "string",
  "label": "string",
  "path": "string|null",
  "pluginId": "string|null"
}
```

### MetricValue

```json
{
  "metricId": "string",
  "value": 123,
  "aggregation": "mean"
}
```

`value` may be number, string, boolean, or null.

## 3. Endpoints

### GET /api/v1/status

**operationId**: `getStatusV1`  
**Tag**: `System`

Response `200`:

```json
{
  "projectId": "string|null",
  "branch": "string|null",
  "storePresent": true,
  "writerActive": false,
  "commitCount": 0,
  "apiStatus": "experimental"
}
```

`apiStatus` values: `experimental`, `baselineReady`, `stable`.

### GET /api/v1/ui/config

**operationId**: `getUiConfigV1`  
**Tag**: `UI Configuration`

Response `200`: `UiConfig` from `data-model.md`.

Required top-level fields:

```json
{
  "schemaVersion": 1,
  "profile": {},
  "plugins": [],
  "capabilities": [],
  "pages": [],
  "entityKinds": [],
  "metrics": [],
  "relationTypes": [],
  "lineCategories": [],
  "visualEncodings": [],
  "graphLenses": [],
  "tables": [],
  "queries": []
}
```

### GET /api/v1/commits

**operationId**: `listCommitsV1`  
**Tag**: `Commits`

Response `200`:

```json
{
  "items": [
    {
      "commitId": "string",
      "commitOrder": 1,
      "authoredAt": "2026-07-08T12:00:00Z",
      "summary": "string|null"
    }
  ]
}
```

### GET /api/v1/entities

**operationId**: `listEntitiesV1`  
**Tag**: `Entities`

Query parameters:

- `entityKindId`: string, required
- `commitId`: string, optional
- `limit`: integer, optional, default `5000`, min `1`, max `10000`

Response `200`:

```json
{
  "entityKindId": "string",
  "commitId": "string|null",
  "items": [
    {
      "id": "string",
      "kind": "string",
      "label": "string",
      "path": "string|null",
      "pluginId": "string|null",
      "selectable": true,
      "reason": null
    }
  ]
}
```

### GET /api/v1/graph

**operationId**: `getGraphV1`  
**Tag**: `Graph`

Query parameters:

- `lensId`: string, required
- `commitId`: string, optional
- `includeZeroWeight`: boolean, optional, default `false`

Response `200`:

```json
{
  "commitId": "string",
  "lensId": "string",
  "nodes": [
    {
      "entity": {
        "id": "string",
        "kind": "string",
        "label": "string",
        "path": null,
        "pluginId": null
      },
      "metrics": [
        { "metricId": "lines.total", "value": 100, "aggregation": null }
      ],
      "distributions": [],
      "attributes": {},
      "lineCounts": {}
    }
  ],
  "edges": [
    {
      "id": "string",
      "source": { "id": "string", "kind": "string", "label": "string" },
      "target": { "id": "string", "kind": "string", "label": "string" },
      "relationTypeId": "string",
      "metrics": [],
      "contributions": [],
      "attributes": {}
    }
  ]
}
```

### GET /api/v1/tables

**operationId**: `listTablesV1`  
**Tag**: `Tables`

Response `200`:

```json
{
  "items": [
    {
      "id": "string",
      "label": "string",
      "description": "string|null",
      "entityKindId": "string|null",
      "supportedActions": [],
      "defaultSort": null
    }
  ]
}
```

### GET /api/v1/tables/{tableId}

**operationId**: `getTableV1`  
**Tag**: `Tables`

Path parameters:

- `tableId`: string, required

Query parameters:

- `commitId`: string, optional
- `parentEntityId`: string, optional
- `limit`: integer, optional, default `500`, min `1`, max `5000`

Response `200`:

```json
{
  "tableId": "string",
  "title": "string",
  "commitId": "string|null",
  "columns": [
    {
      "id": "string",
      "label": "string",
      "valueType": "string",
      "metricId": null,
      "format": null,
      "sortable": true,
      "visibleByDefault": true,
      "align": "left",
      "width": null
    }
  ],
  "rows": [
    {
      "id": "string",
      "cells": {},
      "actions": []
    }
  ]
}
```

### GET /api/v1/metrics/timeseries

**operationId**: `getMetricTimeseriesV1`  
**Tag**: `Metrics`

Query parameters:

- `entityKindId`: string, required
- `metricId`: string, required
- `aggregation`: string, required
- `targetId`: string, optional

Response `200`:

```json
{
  "entityKindId": "string",
  "metricId": "string",
  "aggregation": "mean",
  "targetId": "string|null",
  "series": [
    {
      "label": "string",
      "points": [
        {
          "commitId": "string",
          "commitOrder": 1,
          "value": 123
        }
      ]
    }
  ]
}
```

### GET /api/v1/metrics/hotspots

**operationId**: `getMetricHotspotsV1`  
**Tag**: `Metrics`

Query parameters:

- `entityKindId`: string, required
- `metricId`: string, required
- `aggregation`: string, required
- `rankBy`: `value` or `growth`, required
- `limit`: integer, optional, default `20`, min `1`, max `100`

Response `200`:

```json
{
  "entityKindId": "string",
  "metricId": "string",
  "aggregation": "mean",
  "rankBy": "value",
  "items": [
    {
      "entity": { "id": "string", "kind": "string", "label": "string" },
      "current": 100,
      "first": 50,
      "growth": 50
    }
  ]
}
```

## 4. Explicitly Forbidden in /api/v1 Generic DTOs

The following fields MUST NOT be required public/generic DTO fields:

```text
module_name
python_file_count
cyclomatic
cognitive
jones
manifest_depends
model_reuse
field_property
extension_or_method
python_lines
xml_lines
score_in
score_out
```

They may appear only as metric ids, attribute ids, legacy DTO fields, or plugin-defined ids referenced through definitions.

## 5. Implementation Notes That Are Part of the Contract

- Query parameter names are also `camelCase` where they represent public API names: `entityKindId`, `commitId`, `includeZeroWeight`, `targetId`, `rankBy`, `parentEntityId`.
- Endpoint responses must not return bare arrays. Use an object wrapper with `items`, `nodes`, `edges`, `rows`, or `series` as shown above.
- Every response example in this file is shape-normative. Implementers may add optional fields only if they are documented in OpenAPI and do not require generic frontend branching on PPI/Odoo concepts.
- Error responses must use HTTP status codes appropriate to the failure and the `ErrorResponse` body shape. At minimum: `400` for invalid query, `404` for missing table/lens/entity kind, `409` for unavailable store or active writer conflict when applicable, and `500` for unexpected errors.
- The OpenAPI document must expose `camelCase` schema properties. A test must fail if any public `/api/v1` schema property contains `_`.
- If a route uses FastAPI dependencies or Pydantic aliases, generated OpenAPI must still show the public names from this contract.
- `GET /api/v1/entities` is the dashboard target-list endpoint required by FR-056.
- `GET /api/v1/tables/{tableId}` is the only initial generic table drilldown endpoint. Drilldowns are represented by `targetTableId` plus `params`; no additional table-specific route should be created for the first implementation.
- `commitOrder` is a unique integer assigned at commit ingestion, monotonically increasing in repository history order. When a latest commit is needed, choose the greatest `commitOrder`. If the requested commit is absent from the store, return `ErrorResponse` with code `STORE_NOT_READY`.
