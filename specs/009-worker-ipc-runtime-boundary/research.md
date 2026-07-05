# Research: Worker IPC Runtime Boundary

## R-001: Local IPC transport

**Decision**: Use Unix domain sockets for Linux/macOS MVP local IPC.

**Rationale**: PPI is a local developer tool. Unix sockets avoid opening network ports, work well for same-machine process communication, and match the requirement that internal worker communication should not require public ports.

**Alternatives considered**:

- Local TCP: simpler cross-platform but opens a port and needs extra port selection/security handling.
- stdio JSON-RPC: useful for short-lived child process communication but awkward for singleton long-lived worker with multiple clients.
- Named pipes on Windows: future fallback, not required for first Unix-like MVP.

## R-002: Encoding format

**Decision**: Use MessagePack encoded with `msgspec`.

**Rationale**: Existing architecture direction already selects `msgspec` for typed contracts. MessagePack is compact, binary, and suitable for socket byte streams. `msgspec.Struct` allows explicit request/response/event schemas.

**Alternatives considered**:

- JSON: easier to debug but larger and less aligned with planned msgspec MessagePack IPC.
- Pickle: unsafe for cross-process command boundaries.
- Protobuf: strong schema but introduces more tooling and generation overhead than needed for MVP.

## R-003: Message framing

**Decision**: Use 4-byte unsigned big-endian length-prefix framing.

**Rationale**: Sockets are byte streams and do not preserve message boundaries. Length-prefix framing is simple, deterministic, and reusable for future TCP transport.

**Alternatives considered**:

- Newline-delimited JSON: unsuitable for binary MessagePack.
- MessagePack streaming decoder only: possible, but explicit frame limits and error handling are clearer with a length prefix.
- HTTP/WebSocket: too heavy for local worker IPC MVP.

## R-004: Worker startup race prevention

**Decision**: Use a per-workspace startup lock plus a second health check after acquiring the lock.

**Rationale**: Two clients may start a worker concurrently. A lock prevents duplicate startup, while the second health check handles the case where another process started a healthy worker just before or while the lock was being acquired.

**Alternatives considered**:

- Runtime metadata only: unsafe because stale metadata and races are possible.
- Always kill existing process: dangerous and can interrupt active analysis.
- Rely on storage lock only: too late; duplicate workers may already have initialized conflicting runtime state.

## R-005: Event persistence

**Decision**: Do not persist or replay events in MVP.

**Rationale**: The spec requires live notifications only. Clients recover after reconnect by calling `analysis.status`. This avoids event log storage and replay ordering complexity.

**Alternatives considered**:

- Persistent event log in storage: useful later for audit/replay but out of scope.
- In-memory replay buffer: adds edge cases and still does not survive worker restart.

## R-006: Analysis already running behavior

**Decision**: Return successful `analysis.start` response with `state=already_running` and the active `run_id` for duplicate starts.

**Rationale**: This is easier for CLI/web/IDE clients to handle as an idempotent start request and avoids treating normal multi-client behavior as an error.

**Alternatives considered**:

- Return `ANALYSIS_ALREADY_RUNNING` error: rejected for MVP because duplicate start is a normal idempotent multi-client case.

## R-007: Query dispatch

**Decision**: Use whitelisted named queries for `query.execute`.

**Rationale**: The worker must not become an arbitrary SQL/file execution endpoint. Named queries keep the IPC boundary controlled and make permission/security checks easier.

**Alternatives considered**:

- Raw SQL over IPC: powerful but unsafe and harder to validate.
- One command per query: type-safe but can grow too quickly before plugin/query registry exists.

## R-008: Remote worker compatibility

**Decision**: Keep command semantics transport-independent and do not implement TCP in this feature. Future remote worker usage uses TCP over SSH tunnel/private network, not public worker exposure.

**Rationale**: This preserves the architecture direction without adding security complexity to the local IPC MVP and keeps the implementation local-only.

**Alternatives considered**:

- Implement TLS/mTLS now: overkill for current local developer tool.
- Implement public reverse WebSocket connector: explicitly removed from scope.
