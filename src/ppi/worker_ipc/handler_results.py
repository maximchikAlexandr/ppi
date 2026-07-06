"""Frozen msgspec result types for worker runtime handlers.

Each handler returns one of these structs. The server maps them to
``WorkerResponse`` at the IPC boundary.
"""
from __future__ import annotations

from typing import Any

import msgspec


class HandlerResult(msgspec.Struct, frozen=True, kw_only=True):
    """Base marker for handler return values."""


class HealthResult(HandlerResult):
    worker_id: str
    workspace_id: str
    protocol_version: str
    state: str
    started_at: str


class WorkspaceInfoResult(HandlerResult):
    workspace_id: str
    project_path: str
    analysis_path: str
    profile: str
    display_name: str


class AnalysisStatusResult(HandlerResult):
    state: str
    current_run_id: str | None
    last_run_id: str | None
    progress_percent: float | None
    message: str


class AnalysisStartResult(HandlerResult):
    run_id: str
    accepted: bool
    state: str
    message: str


class AnalysisCancelResult(HandlerResult):
    accepted: bool
    run_id: str | None
    message: str


class ShutdownResult(HandlerResult):
    accepted: bool
    message: str
    error_code: str | None = None


class QueryExecuteResultBody(HandlerResult):
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool


class WorkerErrorResult(HandlerResult):
    """Generic worker error result used for any error code (WORKER_BUSY,
    UNKNOWN_QUERY, STORAGE_UNAVAILABLE, QUERY_FAILED, etc.).
    """

    error_code: str
    message: str


class EventsSubscribeResult(HandlerResult):
    subscription_id: str
    accepted_event_types: list[str] | None
