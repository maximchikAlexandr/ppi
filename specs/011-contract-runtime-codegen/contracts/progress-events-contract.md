# Contract: Progress Events

## Source of truth

```text
src/ppi/runtime/progress.py::ProgressEvent
```

The source must be a tagged/discriminated union of Python `msgspec.Struct` event types.

## Generated files

```text
contracts/progress-events.schema.json
src/ppi/generated/progress_events_schema.py
frontend/src/generated/progressEvents.ts
frontend/src/generated/progressEventValidators.ts
vscode-extension/src/generated/progressEvents.ts
vscode-extension/src/generated/progressEventValidators.ts
docs/generated/progress-events.md
```

## Facades

```text
src/ppi/contracts/progress_events.py
frontend/src/contracts/progressEvents.ts
vscode-extension/src/contracts/progressEvents.ts
```

## Runtime validation

TypeScript consumers must validate unknown JSON using Ajv validators derived from the generated JSON Schema.

Manual type guards and Zod schemas are not allowed as source of truth for this boundary.
