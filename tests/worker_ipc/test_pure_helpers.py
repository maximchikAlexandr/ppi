import pytest

from ppi.worker_ipc.pure_helpers import (
    QueryCliOptions,
    analysis_mode_from_rebuild,
    cli_metric_to_query_payload,
    parse_endpoint,
    progress_percent,
    worker_start_payload_from_cli,
)


def test_analysis_mode_from_rebuild() -> None:
    assert analysis_mode_from_rebuild(True) == "rebuild"
    assert analysis_mode_from_rebuild(False) == "incremental"


def test_progress_percent_normal() -> None:
    assert progress_percent(50, 100) == 50.0
    assert progress_percent(1, 3) == pytest.approx(33.333, rel=1e-3)
    assert progress_percent(5, 0) is None


def test_progress_percent_zero_total() -> None:
    assert progress_percent(0, 0) is None


def test_parse_endpoint_unix() -> None:
    ep = parse_endpoint("unix:///tmp/foo.sock")
    assert ep.transport == "unix"
    assert ep.path == "/tmp/foo.sock"


def test_parse_endpoint_unsupported() -> None:
    with pytest.raises(ValueError):
        parse_endpoint("tcp://localhost:1234")


def test_worker_start_payload_default() -> None:
    assert worker_start_payload_from_cli("") == {"reason": "cli"}


def test_worker_start_payload_with_reason() -> None:
    assert worker_start_payload_from_cli("user click") == {"reason": "user click"}


def test_cli_metric_timeseries_module() -> None:
    opts = QueryCliOptions(metric="metrics/timeseries", module_name="m1", agg="sum")
    payload = cli_metric_to_query_payload("metrics/timeseries", opts)
    assert payload["name"] == "m1"
    assert payload["agg"] == "sum"
    assert payload["level"] == "module"


def test_cli_metric_timeseries_file() -> None:
    opts = QueryCliOptions(metric="metrics/timeseries", file_path="models/foo.py", agg="mean")
    payload = cli_metric_to_query_payload("metrics/timeseries", opts)
    assert payload["name"] == "models/foo.py"
    assert payload["level"] == "file"
    assert payload["agg"] == "mean"


def test_cli_metric_other() -> None:
    opts = QueryCliOptions(
        metric="hotspots",
        commit_hash="abc123",
        include_zero_score=True,
        limit=10,
    )
    payload = cli_metric_to_query_payload("hotspots", opts)
    assert payload["commit"] == "abc123"
    assert payload["include_zero_score"] is True
    assert payload["limit"] == 10
