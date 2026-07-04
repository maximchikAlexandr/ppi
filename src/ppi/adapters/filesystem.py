"""Filesystem path check effect adapters.

Wraps filesystem operations into ``StageResult``-returning functions so
pipeline stages never directly perform IO.
"""

from __future__ import annotations

from pathlib import Path

from expression.core.result import Error, Ok

from ppi.rop.errors import OrchestrationFailure
from ppi.rop.types import StageResult


def path_exists_adapter(path: Path) -> StageResult[bool, OrchestrationFailure]:
    """Check if a filesystem path exists.

    Returns ``Ok(True)`` or ``Ok(False)`` — existence checks are never
    orchestration failures; we treat permission-denied or similar OS
    errors as non-existence for the pipeline boundary.
    ponytail: elevated OS errors become ``Ok(False)``; capture and
    reify them when callers need to distinguish "does not exist" from
    "cannot check".
    """
    try:
        return Ok(path.exists())
    except OSError:
        return Ok(False)


def is_directory_adapter(path: Path) -> StageResult[bool, OrchestrationFailure]:
    """Check if a path is an existing directory."""
    try:
        return Ok(path.is_dir())
    except OSError:
        return Ok(False)


def read_text_file_adapter(path: Path) -> StageResult[str, OrchestrationFailure]:
    """Read a text file from disk (effect adapter)."""
    try:
        return Ok(path.read_text(encoding="utf-8", errors="replace"))
    except OSError as exc:
        return Error(
            OrchestrationFailure(
                stage="read_text_file",
                message=str(exc),
                safe_input_id=str(path),
                cause=exc,
            )
        )


def rglob_files_adapter(
    path: Path,
    pattern: str,
) -> StageResult[list[Path], OrchestrationFailure]:
    """Recursively glob files matching a pattern (effect adapter)."""
    try:
        return Ok(list(sorted(path.rglob(pattern))))
    except OSError as exc:
        return Error(
            OrchestrationFailure(
                stage="rglob_files",
                message=str(exc),
                safe_input_id=str(path),
                cause=exc,
            )
        )
