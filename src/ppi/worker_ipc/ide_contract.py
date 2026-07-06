"""IDE bridge contract.

Defines the supported worker IPC commands for IDE/extension integrations.
Legacy `ppi rpc` paths remain for backward compatibility, but new IDE
integrations should target the worker IPC boundary.
"""
from __future__ import annotations


SUPPORTED_IDE_WORKER_COMMANDS: tuple[str, ...] = (
    "worker.health",
    "workspace.info",
    "analysis.status",
    "analysis.start",
    "analysis.cancel",
    "query.execute",
    "events.subscribe",
)
