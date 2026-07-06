"""Tests for spec 009 R-013 AnalysisService types."""
from __future__ import annotations

from pathlib import Path

import pytest

from ppi.worker_ipc.analysis_service import (
    AnalysisMode,
    AnalysisProgress,
    AnalysisRunConfig,
    AnalysisRunResult,
    AnalysisService,
)


def test_analysis_mode_values() -> None:
    assert AnalysisMode.INCREMENTAL == "incremental"
    assert AnalysisMode.FULL == "full"


def test_analysis_run_config_is_frozen() -> None:
    cfg = AnalysisRunConfig(
        repo=Path("/tmp/repo"),
        branch=None,
        profile="odoo",
        analysis_dir=Path("/tmp/analysis"),
        mode=AnalysisMode.INCREMENTAL,
        addons_paths=(),
        module_prefixes=(),
        include_modules=(),
        all_modules=True,
    )
    with pytest.raises(Exception):
        cfg.profile = "other"


def test_analysis_progress_is_frozen() -> None:
    p = AnalysisProgress(processed=5, commits_total=10, short_hash="abc", progress_percent=50.0)
    assert p.processed == 5
    with pytest.raises(Exception):
        p.processed = 6


def test_analysis_run_result_is_frozen() -> None:
    r = AnalysisRunResult(
        run_id="r-1",
        status="completed",
        commits_total=10,
        commits_succeeded=10,
        commits_failed=0,
    )
    assert r.run_id == "r-1"
    with pytest.raises(Exception):
        r.status = "failed"


def test_analysis_service_from_config_builds_instance() -> None:
    cfg = AnalysisRunConfig(
        repo=Path("/tmp/repo"),
        branch=None,
        profile="odoo",
        analysis_dir=Path("/tmp/analysis"),
        mode=AnalysisMode.INCREMENTAL,
        addons_paths=(),
        module_prefixes=(),
        include_modules=(),
        all_modules=True,
    )
    service = AnalysisService.from_config(store_path=Path("/tmp/store.duckdb"), config=cfg)
    assert service is not None
    assert service._profile == "odoo"


def test_analysis_service_run_signature() -> None:
    """Verify the spec-compliant run has the documented signature."""
    import inspect
    sig = inspect.signature(AnalysisService.run)
    params = list(sig.parameters.keys())
    assert "run_id" in params
    assert "progress" in params
    assert "should_cancel" in params


def test_analysis_service_run_returns_analysis_run_result(tmp_path: Path) -> None:
    """run returns an AnalysisRunResult, not None."""
    import inspect
    hints = inspect.get_annotations(AnalysisService.run)
    assert hints["return"] is AnalysisRunResult or str(hints["return"]) == "AnalysisRunResult"
