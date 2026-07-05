from pathlib import Path

import pytest

from ppi.runtime.lock import LockBusyError
from ppi.runtime.lock import write_lock as worker_startup_lock


def test_acquire_release(tmp_path: Path) -> None:
    lock_file = tmp_path / "worker.lock"
    with worker_startup_lock(lock_file):
        assert lock_file.is_file()
    assert not lock_file.is_file()


def test_contended_lock(tmp_path: Path) -> None:
    lock_file = tmp_path / "worker.lock"
    with worker_startup_lock(lock_file):
        with pytest.raises(LockBusyError):
            with worker_startup_lock(lock_file):
                pass
