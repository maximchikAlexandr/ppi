"""Git history ingestion effect adapter.

Wraps Git operations (log, rev-list, branch listing) into
``StageResult``-returning adapters for the history railway.
"""

from __future__ import annotations

from pathlib import Path

from expression.core.result import Error, Ok

from ppi.rop.errors import OrchestrationFailure
from ppi.rop.types import StageResult


def git_history_ingestion_pipeline(
    repo_path: Path,
    max_count: int = 100,
) -> StageResult[str, OrchestrationFailure]:
    """Spec-named pipeline: ingest git history log."""
    return git_log_adapter(repo_path, max_count)


def git_log_adapter(
    repo_path: Path,
    max_count: int = 100,
) -> StageResult[str, OrchestrationFailure]:
    """Read Git log output for a repository.

    Returns the raw log output as a string for downstream parsing.
    """
    try:
        import subprocess

        result = subprocess.run(
            ["git", "log", f"--max-count={max_count}", "--format=%H %at %s"],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )
        if result.returncode != 0:
            return Error(
                OrchestrationFailure(
                    stage="git_log",
                    message=result.stderr.strip(),
                    safe_input_id=str(repo_path),
                )
            )
        return Ok(result.stdout)
    except FileNotFoundError:
        return Error(
            OrchestrationFailure(
                stage="git_log",
                message="Git executable not found",
                safe_input_id=str(repo_path),
            )
        )
