"""Typed error taxonomy for the ROP migration.

Five error categories matching the Railway Oriented Pipeline Migration
spec (PI-008):

* ``ValidationFailure`` — bad input/config/path/schema; short-circuits.
* ``RecoverableDomainFailure`` — parse/module-level issue in analysis output.
* ``OrchestrationFailure`` — Git/worktree/process/RPC/cancellation; short-circuits.
* ``DecodeMappingFailure`` — TypeScript transport/schema/domain conversion error.
* ``BridgeFailure`` — VS Code workspace/settings/process/RPC/webview error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationFailure:
    stage: str
    message: str
    safe_input_id: str = ""
    details: tuple[tuple[str, Any], ...] = ()
    cause: BaseException | None = None


@dataclass(frozen=True, slots=True)
class RecoverableDomainFailure:
    stage: str
    message: str
    safe_input_id: str = ""
    details: tuple[tuple[str, Any], ...] = ()
    cause: BaseException | None = None


@dataclass(frozen=True, slots=True)
class OrchestrationFailure:
    stage: str
    message: str
    safe_input_id: str = ""
    details: tuple[tuple[str, Any], ...] = ()
    cause: BaseException | None = None


@dataclass(frozen=True, slots=True)
class DecodeMappingFailure:
    stage: str
    message: str
    safe_input_id: str = ""
    details: tuple[tuple[str, Any], ...] = ()
    cause: BaseException | None = None


@dataclass(frozen=True, slots=True)
class BridgeFailure:
    stage: str
    message: str
    safe_input_id: str = ""
    details: tuple[tuple[str, Any], ...] = ()
    cause: BaseException | None = None


TypedStageError = (
    ValidationFailure
    | RecoverableDomainFailure
    | OrchestrationFailure
    | DecodeMappingFailure
    | BridgeFailure
)

__all__ = [
    "TypedStageError",
    "ValidationFailure",
    "RecoverableDomainFailure",
    "OrchestrationFailure",
    "DecodeMappingFailure",
    "BridgeFailure",
]
