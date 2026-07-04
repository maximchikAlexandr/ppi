# Research: Railway Oriented Pipeline Migration

**Spec ID**: `008-rop-pipeline-migration`  
**Date**: 2026-07-04

## Decision 1: Python ROP library

**Decision**: Use the existing `Expression` dependency as the default and only Python ROP library for this feature.

**Rationale**: The project and constitution already standardize on `Expression` for `Result`, `Option`, and typed `pipe`. Adding `returns` would create a second Result/Option vocabulary and force weak implementers to bridge two similar abstractions. Effectful Python boundaries should stay boring: catch known external failures at adapters and return `Expression` `Result` values.

**Alternatives considered**:

- `toolz.pipe`: already useful for value piping, but too weak for typed failure/effect channels by itself.
- `returns`: capable ROP library, but rejected here because the project already has `Expression` and the constitution names it as a fixed dependency.
- Handwritten `Result`/pipe helpers: rejected because the feature explicitly prefers mature FP libraries over custom primitives.
- `dry-python/classes` or small custom monads: rejected as either less directly aligned or likely to increase custom abstraction surface.

## Decision 2: TypeScript primary library

**Decision**: Use `Effect` as the TypeScript library for API/RPC/bridge/effectful flows, with pure derivation stages written as plain typed functions or Effect-provided `Either`/`Option` primitives where a full effect is unnecessary.

**Rationale**: The TypeScript side includes async reads, JSON-RPC/transport errors, schema decoding, possible cancellation, resource-ish bridge/process lifecycle, and UI-facing typed errors. Effect models workflows that can succeed or fail, tracks errors and context in the type system, and includes docs for error management, resource management, concurrency, streams, schema, and building pipelines. That fits the desired full ROP migration better than a Result-only library.

**Alternatives considered**:

- `fp-ts`: strong typed FP foundation with `Either`, `TaskEither`, `ReaderTaskEither`, `Option`, `pipe`, and type classes. Rejected for this feature to avoid a second TypeScript FP vocabulary beside Effect.
- `neverthrow`: attractive for a small Result-only migration, but too narrow for bridge/read/runtime flows with async, resource, cancellation, schema, and environment/context needs.
- Handwritten TS pipe/result helpers: rejected to avoid recreating a partial FP library.

## Decision 3: Error taxonomy

**Decision**: Use a shared domain-level taxonomy rather than one generic `PipelineError`.

**Rationale**: The migration must preserve distinct semantics: validation failures should short-circuit, recoverable module/file/facts issues should remain analysis data, orchestration failures should abort the relevant history/process railway, decode/mapping failures should reach UI cleanly, and bridge failures should be displayable/actionable in VS Code.

**Alternatives considered**:

- One catch-all error: rejected because it hides recovery/reporting intent.
- Raw exceptions with stage tags: rejected because it still relies on exception tunneling rather than typed railway failures.
- Separate unrelated error shapes per module: rejected because cross-boundary mapping would become inconsistent.

## Decision 4: Framework/object shells

**Decision**: Keep framework/object primitives at the edge, but require named function adapters when the pipeline calls them.

**Rationale**: AST visitors, React components, VS Code APIs, process handles, storage drivers, and CLI framework objects are naturally object/lifecycle/effect-based. Forcing them into pure FP would reduce clarity. The full migration bar is satisfied when these shells are isolated, typed at the boundary, and prevented from leaking into the core pipeline state.

**Alternatives considered**:

- Rewrite all object code as pure FP: rejected as unnecessary and risky.
- Leave object code mixed into core flows: rejected because it prevents full ROP migration and testability.

## Decision 5: Migration order

**Decision**: Start with Python `odoo_project_analysis_pipeline`, then module enrichment, then history/effects, then TypeScript read/view-models, then VS Code bridge, then cleanup.

**Rationale**: The Odoo analysis core is already close to a stage pipeline and is the central product value path. Migrating it first establishes the vocabulary and proves the approach before taking on harder effect shells and frontend bridge boundaries.

**Alternatives considered**:

- Start with TypeScript UI: rejected because backend pipeline vocabulary and output semantics drive much of the frontend domain model.
- Start with VS Code bridge: rejected because it is mostly orchestration/effects and would make the migration look like adapter cleanup rather than core ROP.
- Big-bang migration: rejected because compatibility and characterization safety are requirements.

## Decision 6: Anti-cosmetic acceptance gate

**Decision**: Add an explicit anti-cosmetic gate: a covered process is not migrated if it only has a top-level pipe wrapper around unchanged imperative internals.

**Rationale**: The user explicitly requested a full ROP migration, not a formal refactoring. This gate prevents an implementation from satisfying naming/style requirements while leaving exception-driven, nullable, hidden-mutating control flow intact.

**Alternatives considered**:

- Rely on code review: insufficient because the spec must define measurable completion.
- Only count files/functions renamed to `pipeline`: rejected as meaningless.
