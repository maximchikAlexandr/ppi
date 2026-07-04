"""Regression tests for file-level hotspot queries."""

from __future__ import annotations

from pathlib import Path

from ppi.core.contracts import AnalysisBatch, CommitRef, Distribution, FileMetrics
from ppi.query.contracts import QueryParams
from ppi.query.pipeline import run_query
from ppi.storage.writer import StoreWriter


def _commit() -> CommitRef:
    return CommitRef(
        commit_hash="c" * 40,
        commit_order=0,
        author_name="Test",
        author_email="test@example.com",
        authored_at=1,
        committed_at=1,
        summary="init",
    )


def _distribution() -> Distribution:
    return Distribution(count=1, mean=4.0, median=4.0, p95=4.0, max=4.0)


def test_file_hotspots_do_not_require_module_total_lines(tmp_path: Path) -> None:
    """File metrics table has no total_lines column, but file hotspots still work."""
    store_file = tmp_path / "history.duckdb"
    writer = StoreWriter(store_file)
    try:
        writer.write_batch(
            AnalysisBatch(
                commit=_commit(),
                files=(
                    FileMetrics(
                        module_name="demo_module",
                        relative_path="models/demo.py",
                        line_category_id="python",
                        metrics={"cyclomatic_mean": 4.0},
                        line_counts={"python_lines": 12},
                        distributions={"cyclomatic": _distribution()},
                    ),
                ),
                modules=(),
                edges=(),
                failures=(),
            ),
            "run-1",
        )
    finally:
        writer.close()

    result = run_query(
        store_file,
        QueryParams(
            metric="hotspots",
            level="file",
            metric_id="cyclomatic",
            agg="mean",
        ),
    )

    assert result.is_ok()
    assert result.ok == [
        {
            "name": "demo_module/models/demo.py",
            "current": 4.0,
            "first": None,
            "growth": None,
        },
    ]
