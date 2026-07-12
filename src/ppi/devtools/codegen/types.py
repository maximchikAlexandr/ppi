from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationIssue:
    source_id: str
    message: str
    severity: str = "error"
