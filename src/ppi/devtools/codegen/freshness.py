from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FreshnessReport:
    status: str
    stale_files: tuple[Path, ...] = field(default_factory=tuple)
    missing_files: tuple[Path, ...] = field(default_factory=tuple)
    remediation_command: str = "uv run ppi dev generate-contracts"

    @property
    def passed(self) -> bool:
        return self.status == "fresh"


def check_file_freshness(committed: Path, regenerated: str) -> bool:
    if not committed.is_file():
        return False
    return committed.read_text(encoding="utf-8") == regenerated
