"""Contract tests for the ``ppi analyze --json`` progress stream (FR-019)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from ppi.cli.main import cli
from ppi.runtime.progress import (
    CommitProgress,
    RunCompleted,
    RunFailed,
    RunStarted,
    decode_line,
)
from ppi.worker_ipc.protocol import AnalysisStartRequest


def _events(output: str):
    """Decode the JSON-lines emitted on stdout into event structs, skipping non-JSON noise."""
    events = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(decode_line(line))
        except Exception:  # noqa: BLE001
            continue
    return events


@pytest.mark.asyncio
async def test_json_analysis_waits_for_event_stream_ready_before_start() -> None:
    """No analysis event can be lost while the stream subscription is pending."""
    from ppi.cli.main import _analyze_via_worker

    allow_ready = asyncio.Event()

    class _Client:
        started = False

        async def health(self):
            return {"events_stream_ready_handshake": True}

        async def events_stream(self, _types, *, ready=None):
            await allow_ready.wait()
            assert ready is not None
            ready.set()
            if False:
                yield None

        async def analysis_start(self, _request):
            self.started = True
            return {"state": "running", "run_id": "r"}

        async def analysis_status(self):
            return {"state": "completed", "commits_total": 0}

        async def close(self):
            return None

    client = _Client()
    task = asyncio.create_task(
        _analyze_via_worker(client, AnalysisStartRequest(branch="main"), True),
    )
    await asyncio.sleep(0.2)
    assert not client.started
    allow_ready.set()
    await task
    assert client.started


@pytest.mark.asyncio
async def test_json_analysis_uses_legacy_stream_without_handshake() -> None:
    from ppi.cli.main import _analyze_via_worker

    class _Client:
        started = False
        stream_requested_ready = False

        async def health(self):
            return {}

        async def events_stream(self, _types, *, ready=None):
            self.stream_requested_ready = ready is not None
            if False:
                yield None

        async def analysis_start(self, _request):
            self.started = True
            return {"state": "running", "run_id": "legacy"}

        async def analysis_status(self):
            return {"state": "completed", "commits_total": 0}

        async def close(self):
            return None

    client = _Client()
    await _analyze_via_worker(client, AnalysisStartRequest(branch="main"), True)
    assert client.started
    assert not client.stream_requested_ready


def test_analyze_json_emits_ordered_terminal_stream(mini_repo: Path, tmp_path: Path):
    """``--json`` emits run_started -> commit_progress* -> run_completed and no human output."""
    runner = CliRunner()
    analysis_dir = tmp_path / "analysis"
    result = runner.invoke(
        cli,
        [
            "--repo",
            str(mini_repo),
            "--branch",
            "HEAD",
            "--analysis-dir",
            str(analysis_dir),
            "analyze",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    events = _events(result.output)
    assert events, "expected at least one progress event"
    assert isinstance(events[0], RunStarted)
    started = events[0]
    assert started.branch
    assert started.mode in ("incremental", "rebuild")
    assert started.commits_total >= 1

    progress_events = [e for e in events if isinstance(e, CommitProgress)]
    assert progress_events, "expected at least one commit_progress event"
    assert [p.processed for p in progress_events] == list(
        range(1, len(progress_events) + 1)
    )
    for p in progress_events:
        assert p.commits_total == started.commits_total
        assert 0 < p.processed <= p.commits_total
        assert len(p.short_hash) == 8
    if len(progress_events) > 1:
        assert len({p.short_hash for p in progress_events}) > 1

    terminal = [e for e in events if isinstance(e, (RunCompleted, RunFailed))]
    assert len(terminal) == 1, "exactly one terminal event is required"
    assert isinstance(terminal[0], RunCompleted)
    completed = terminal[0]
    assert completed.commits_succeeded + completed.commits_failed == len(progress_events)
    assert completed.duration_ms >= 0

    # run_started precedes the first progress event precedes the terminal event
    first_progress = events.index(progress_events[0])
    terminal_index = events.index(terminal[0])
    assert events.index(events[0]) == 0 and isinstance(events[0], RunStarted)
    assert 0 < first_progress < terminal_index


def test_analyze_json_suppresses_human_output(mini_repo: Path, tmp_path: Path):
    """``--json`` must not emit the human progress bar or the summary lines."""
    runner = CliRunner()
    analysis_dir = tmp_path / "analysis"
    result = runner.invoke(
        cli,
        [
            "--repo",
            str(mini_repo),
            "--branch",
            "HEAD",
            "--analysis-dir",
            str(analysis_dir),
            "analyze",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Analyzing " not in result.output
    assert "Store:" not in result.output
    assert "%" not in result.output  # progressbar percentage never rendered


def test_analyze_without_json_keeps_human_output(mini_repo: Path, tmp_path: Path):
    """Without ``--json`` the human-readable summary is unchanged."""
    runner = CliRunner()
    analysis_dir = tmp_path / "analysis"
    result = runner.invoke(
        cli,
        [
            "--repo",
            str(mini_repo),
            "--branch",
            "HEAD",
            "--analysis-dir",
            str(analysis_dir),
            "analyze",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Analyzed " in result.output
    assert "Store:" in result.output
    # No JSON event objects leak into the human output.
    assert '"type":"run_started"' not in result.output


def test_analyze_json_emits_run_failed_with_worker_terminal_state(monkeypatch, mini_repo, tmp_path):
    """A failed worker run remains a parseable JSON-lines terminal event."""
    from ppi.runtime.progress import RunFailed

    class _Client:
        async def health(self):
            return {"events_stream_ready_handshake": True}

        async def analysis_start(self, _request):
            return {"state": "running", "run_id": "run-failed"}

        async def analysis_status(self):
            return {"state": "failed", "message": "worker failed"}

        async def events_stream(self, _event_types, *, ready=None):
            if ready is not None:
                ready.set()
            if False:
                yield None

        async def close(self):
            return None

    class _Gateway:
        def __init__(self, *_args):
            pass

        async def get_client(self, **_kwargs):
            return SimpleNamespace(status="healthy", client=_Client())

    monkeypatch.setattr("ppi.cli.main.WorkerGateway", _Gateway)

    runner = CliRunner()
    analysis_dir = tmp_path / "analysis"
    result = runner.invoke(
        cli,
        [
            "--repo",
            str(mini_repo),
            "--branch",
            "HEAD",
            "--analysis-dir",
            str(analysis_dir),
            "analyze",
            "--json",
        ],
    )
    assert result.exit_code != 0
    events = _events(result.output)
    failed = [e for e in events if isinstance(e, RunFailed)]
    assert len(failed) == 1
    failed_event = failed[0]
    assert failed_event.exit_reason == "unknown"
    assert failed_event.message == "worker failed"
    assert failed_event.stderr_tail == "worker failed"
