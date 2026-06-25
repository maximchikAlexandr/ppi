"""Unit tests for runtime value objects (clock, ids, paths) and serialization."""

from __future__ import annotations

import pytest

from ppi.adapters.serialization import (
    SerializationError,
    batch_from_json,
    batch_to_json,
    decode_batch,
    encode_batch,
)
from ppi.core.contracts import AnalysisBatch, CommitRef
from ppi.runtime.value_objects import (
    AnalysisDir,
    FakeClock,
    ProjectId,
    RunId,
    StorePath,
    SystemClock,
    WorktreeDir,
    WriterLockPath,
)


def _sample_batch() -> AnalysisBatch:
    return AnalysisBatch(
        commit=CommitRef(
            commit_hash="abc",
            commit_order=0,
            author_name="Test",
            author_email="test@example.com",
            authored_at=1,
            committed_at=1,
            summary="init",
        ),
        files=(),
        modules=(),
        edges=(),
        failures=(),
    )


# --- clock -----------------------------------------------------------------


def test_system_clock_positive():
    assert SystemClock().now_epoch() > 0


def test_fake_clock_fixed():
    clock = FakeClock(initial=1000)
    assert clock.now_epoch() == 1000
    assert clock.now_epoch() == 1000


def test_fake_clock_advancing():
    clock = FakeClock(initial=1000, advance_per_call=5)
    assert clock.now_epoch() == 1000
    assert clock.now_epoch() == 1005
    assert clock.now_epoch() == 1010


# --- ids -------------------------------------------------------------------


def test_run_id_ok():
    assert str(RunId.of("abcdef12")) == "abcdef12"


def test_run_id_rejects_non_hex():
    with pytest.raises(ValueError):
        RunId.of("not-hex")


def test_project_id_ok():
    assert str(ProjectId.of("abcdef1234567890")) == "abcdef1234567890"


def test_project_id_rejects_wrong_length():
    with pytest.raises(ValueError):
        ProjectId.of("short")


# --- paths -----------------------------------------------------------------


def test_analysis_dir_ok(tmp_path):
    assert str(AnalysisDir.of(tmp_path)) == str(tmp_path)


def test_analysis_dir_rejects_relative():
    with pytest.raises(ValueError):
        AnalysisDir.of("relative")


def test_store_path_ok(tmp_path):
    p = tmp_path / "history.duckdb"
    assert str(StorePath.of(p)) == str(p)


def test_store_path_rejects_relative():
    with pytest.raises(ValueError):
        StorePath.of("rel")


def test_writer_lock_path_ok(tmp_path):
    assert str(WriterLockPath.of(tmp_path / "writer.lock")) == str(tmp_path / "writer.lock")


def test_worktree_dir_ok(tmp_path):
    assert str(WorktreeDir.of(tmp_path / "wt")) == str(tmp_path / "wt")


# --- serialization ---------------------------------------------------------


def test_encode_decode_roundtrip():
    batch = _sample_batch()
    line = encode_batch(batch)
    restored = decode_batch(line)
    assert restored.commit.commit_hash == "abc"


def test_batch_to_json_aliases_match_encode():
    batch = _sample_batch()
    assert batch_to_json(batch) == encode_batch(batch)


def test_batch_from_json_alias_matches_decode():
    line = encode_batch(_sample_batch())
    assert batch_from_json(line).commit.commit_hash == decode_batch(line).commit.commit_hash


def test_decode_batch_invalid_raises_serialization_error():
    with pytest.raises(SerializationError):
        decode_batch("{not json")