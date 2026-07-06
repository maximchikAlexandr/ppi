"""Worker startup lock.

Separate from the writer lock. The writer lock guards storage writes
(``ppi.runtime.lock.write_lock``). The startup lock guards process
spawning only. They are different files and serve different purposes.

Reuses ``ppi.runtime.lock`` primitives for stale-PID detection and
cleanup, but the lock file is unique to the worker IPC layer.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from ppi.runtime.lock import write_lock
from ppi.worker_ipc.runtime_paths import startup_lock_path


@contextmanager
def worker_startup_lock(workspace_id: str) -> Iterator[None]:
    """Acquire the startup lock for ``workspace_id``.

    Raises ``LockBusyError`` (re-exported from ppi.runtime.lock) if
    another process currently holds the lock.
    """
    lock_file = startup_lock_path(workspace_id)

    with write_lock(lock_file):
        yield
