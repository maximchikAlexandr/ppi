"""Pure helper functions for the worker IPC layer.

No IO, no sockets, no filesystem, no subprocess, no globals.
"""
from __future__ import annotations

from dataclasses import dataclass

from ppi.worker_ipc.runtime_paths import Endpoint


def analysis_mode_from_rebuild(rebuild: bool) -> str:
    """Map ``--rebuild`` boolean flag to analysis mode string."""
    return "rebuild" if rebuild else "incremental"


def progress_percent(processed: int, total: int) -> float | None:
    """Compute progress percentage; returns None if total is zero."""
    if total <= 0:
        return None
    return (processed / total) * 100.0


def parse_endpoint(uri: str) -> Endpoint:
    """Parse a ``unix://`` URI into an ``Endpoint``."""
    if not uri.startswith("unix://"):
        raise ValueError(f"unsupported endpoint transport: {uri!r}")
    return Endpoint(transport="unix", path=uri.removeprefix("unix://"))


def worker_start_payload_from_cli(reason: str) -> dict[str, str]:
    """Build the worker.start command payload from CLI options."""
    return {"reason": reason or "cli"}


@dataclass(frozen=True, slots=True)
class QueryCliOptions:
    """Immutable CLI options for the ``query`` command."""

    metric: str
    module_name: str | None = None
    file_path: str | None = None
    commit_hash: str | None = None
    agg: str = "mean"
    include_zero_score: bool = False
    limit: int | None = None
    metric_id: str | None = None
    level: str = "module"


def cli_metric_to_query_payload(metric: str, options: QueryCliOptions) -> dict[str, str | int | bool | None]:
    """Build the query.execute payload from CLI options.

    Pure: no IO, no WorkerClient access, no FastAPI/Click imports.
    """
    if metric == "metrics/timeseries":
        return {
            "level": "file" if options.file_path else "module",
            "metric_id": options.metric_id or metric,
            "name": options.file_path or options.module_name or "",
            "agg": options.agg,
        }
    return {
        "commit": options.commit_hash,
        "include_zero_score": options.include_zero_score,
        "limit": options.limit,
    }
