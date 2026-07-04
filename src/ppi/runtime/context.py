"""Immutable runtime context and boundary handles for analysis pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ppi.core.odoo.pipeline import ReportConfig


@dataclass(frozen=True)
class RuntimeContext:
    repo_path: Path
    analysis_dir: Path
    branch: str
    profile: str
    report_config: ReportConfig
    addons_paths: tuple[str, ...] = ()
    verbose: bool = False
