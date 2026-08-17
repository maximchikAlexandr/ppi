from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

import msgspec

from ppi.core.analyzer import report_config_to_scope
from ppi.core.contracts import ProjectRef, RunMeta, batch_to_json
from ppi.core.odoo.pipeline import build_report_config
from ppi.history import git
from ppi.history.walker import cleanup_worktree, walk_history
from ppi.runtime import lock as project_lock
from ppi.runtime.paths import (
    project_id_from_repo,
    writer_lock_path,
)
from ppi.storage import schema
from ppi.storage.writer import StoreWriter
from ppi.worker_ipc.protocol import (
    AnalysisEffectiveMode,
    AnalysisExitReason,
    AnalysisRequestMode,
    AnalysisStartRequest,
    AnalysisTerminalState,
)

AnalysisMode = AnalysisRequestMode


@dataclass(frozen=True, slots=True)
class AnalysisRunConfig:
    repo: Path
    branch: str | None
    profile: str
    analysis_dir: Path
    mode: AnalysisMode
    addons_paths: tuple[str, ...]
    module_prefixes: tuple[str, ...]
    include_modules: tuple[str, ...]
    all_modules: bool


class AnalysisProgress(msgspec.Struct, frozen=True):
    processed: int
    commits_total: int
    short_hash: str
    progress_percent: float | None
    mode: AnalysisEffectiveMode = AnalysisEffectiveMode.INCREMENTAL


class AnalysisRunResult(msgspec.Struct, frozen=True):
    run_id: str
    status: AnalysisTerminalState
    commits_total: int
    commits_succeeded: int
    commits_failed: int
    mode: AnalysisEffectiveMode = AnalysisEffectiveMode.INCREMENTAL
    exit_reason: AnalysisExitReason | None = None
    error_message: str = ""
    stderr_tail: str = ""


def _batch_succeeded(batch) -> bool:
    if batch.files or batch.modules or batch.edges or not batch.failures:
        return True
    return all(
        failure.error_text.startswith("No matching Odoo modules found under:")
        for failure in batch.failures
    )


class AnalysisService:
    def __init__(
        self,
        store_path: Path,
        project_path: Path,
        analysis_path: Path,
        profile: str = "odoo",
    ) -> None:
        self._store_path = store_path
        self._project_path = project_path
        self._analysis_path = analysis_path
        self._profile = profile

    @classmethod
    def from_config(cls, store_path: Path, config: AnalysisRunConfig) -> AnalysisService:
        """Build an AnalysisService from a frozen ``AnalysisRunConfig``."""
        return cls(
            store_path=store_path,
            project_path=config.repo,
            analysis_path=config.analysis_dir,
            profile=config.profile,
        )

    async def run_legacy(
        self,
        mode: str = "incremental",
        cancel_flag: Callable[[], bool] | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> None:
        """Compatibility adapter for callers that predate typed requests."""

        async def legacy_progress(progress: AnalysisProgress) -> None:
            if progress_callback is not None:
                progress_callback(progress.progress_percent or 0.0, progress.short_hash)

        await self.run(
            run_id=str(uuid.uuid4()),
            request=AnalysisStartRequest(mode=AnalysisRequestMode(mode)),
            progress=legacy_progress if progress_callback is not None else None,
            should_cancel=cancel_flag,
        )

    async def run(
        self,
        run_id: str,
        request: AnalysisStartRequest,
        *,
        progress: Callable[[AnalysisProgress], Awaitable[None]] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> AnalysisRunResult:
        """Spec-compliant run entry point.

        ``progress`` is a callable that receives an ``AnalysisProgress``
        and returns an awaitable. The service awaits it after each batch.

        Returns an ``AnalysisRunResult`` describing the run summary.
        """
        started_at = git.utc_now_epoch()
        branch_result = git.resolve_branch(self._project_path, request.branch)
        if not branch_result.is_ok():
            return AnalysisRunResult(
                run_id=run_id,
                status=AnalysisTerminalState.FAILED,
                commits_total=0,
                commits_succeeded=0,
                commits_failed=0,
                exit_reason=AnalysisExitReason.BAD_WORKSPACE,
                error_message=str(branch_result.error),
                stderr_tail=str(branch_result.error),
            )
        rebuild = request.mode is AnalysisRequestMode.FULL
        project_id = project_id_from_repo(self._project_path)
        branch_name = branch_result.ok

        try:
            with project_lock.write_lock(writer_lock_path(self._project_path)):
                return await self._run_locked(
                    run_id,
                    request,
                    branch_name,
                    project_id,
                    rebuild,
                    started_at,
                    progress,
                    should_cancel,
                )
        except project_lock.LockBusyError as exc:
            return AnalysisRunResult(
                run_id=run_id,
                status=AnalysisTerminalState.FAILED,
                commits_total=0,
                commits_succeeded=0,
                commits_failed=0,
                exit_reason=AnalysisExitReason.LOCK_BUSY,
                error_message=str(exc),
                stderr_tail=str(exc)[-2000:],
            )

    async def _run_locked(
        self,
        run_id: str,
        request: AnalysisStartRequest,
        branch_name: str,
        project_id: str,
        rebuild: bool,
        started_at: int,
        progress: Callable[[AnalysisProgress], Awaitable[None]] | None,
        should_cancel: Callable[[], bool] | None,
    ) -> AnalysisRunResult:
        """Perform every store/worktree operation while the caller owns the writer lock."""
        writer = StoreWriter(self._store_path)
        worktree_owned = False
        run_started = False
        total = succeeded = failed = 0
        status = AnalysisTerminalState.COMPLETED
        try:
            report_config = build_report_config(
                project_label=self._project_path.name,
                module_prefixes=request.module_prefixes,
                include_modules=request.include_modules,
                all_modules=request.all_modules,
            )
            scope = report_config_to_scope(report_config)
            skip_commits: set[str] = set()
            if not rebuild:
                stored = writer.get_project()
                if stored is not None:
                    if stored.project_id != project_id:
                        raise RuntimeError("Repository changed; rerun with --rebuild")
                    if stored.branch != branch_name:
                        rebuild = True
                    elif stored.scope is not None and stored.scope != scope:
                        raise RuntimeError("Module scope changed; rerun with --rebuild")
                if not rebuild:
                    skip_commits = writer.stored_commit_hashes()
            if rebuild:
                writer.clear_project_data()
            writer.upsert_project(
                ProjectRef(
                    project_id=project_id,
                    repo_path=str(self._project_path),
                    branch=branch_name,
                    profile=self._profile,
                    scope=scope,
                )
            )
            writer.start_run(
                RunMeta(
                    run_id=run_id,
                    branch=branch_name,
                    mode="rebuild" if rebuild else "incremental",
                    status="running",
                    started_at=started_at,
                    finished_at=None,
                    commits_total=0,
                    commits_succeeded=0,
                    commits_failed=0,
                )
            )
            run_started = True
            prepared = walk_history(
                self._project_path,
                branch_name,
                self._analysis_path,
                profile=self._profile,
                skip_commits=skip_commits,
                addons_paths=request.addons_paths,
                report_config=report_config,
            )
            if prepared.is_error():
                raise RuntimeError(prepared.error)
            worktree_owned = True
            batches, state = prepared.ok
            total = state.commits_total if state else 0
            jsonl_file = (
                Path(request.jsonl_output).open("w", encoding="utf-8")
                if request.jsonl_output
                else None
            )
            try:
                for processed, batch in enumerate(batches, start=1):
                    if should_cancel is not None and should_cancel():
                        status = AnalysisTerminalState.CANCELLED
                        break
                    writer.write_batch(batch, run_id)
                    if _batch_succeeded(batch):
                        succeeded += 1
                    else:
                        failed += 1
                    if jsonl_file is not None:
                        jsonl_file.write(batch_to_json(batch) + "\n")
                    if progress is not None:
                        await progress(
                            AnalysisProgress(
                                processed=processed,
                                commits_total=total,
                                short_hash=batch.commit.commit_hash[:8],
                                progress_percent=(processed / total) * 100.0 if total else None,
                                mode=AnalysisEffectiveMode.REBUILD
                                if rebuild
                                else AnalysisEffectiveMode.INCREMENTAL,
                            )
                        )
            finally:
                if jsonl_file is not None:
                    jsonl_file.close()
            writer.finish_run(
                RunMeta(
                    run_id=run_id,
                    branch=branch_name,
                    mode="rebuild" if rebuild else "incremental",
                    status=status.value,
                    started_at=started_at,
                    finished_at=git.utc_now_epoch(),
                    commits_total=total,
                    commits_succeeded=succeeded,
                    commits_failed=failed,
                )
            )
            return AnalysisRunResult(
                run_id=run_id,
                status=status,
                commits_total=total,
                commits_succeeded=succeeded,
                commits_failed=failed,
                mode=AnalysisEffectiveMode.REBUILD
                if rebuild
                else AnalysisEffectiveMode.INCREMENTAL,
            )
        except schema.SchemaIncompatibleError as exc:
            return AnalysisRunResult(
                run_id=run_id,
                status=AnalysisTerminalState.FAILED,
                commits_total=total,
                commits_succeeded=succeeded,
                commits_failed=failed,
                mode=AnalysisEffectiveMode.REBUILD
                if rebuild
                else AnalysisEffectiveMode.INCREMENTAL,
                exit_reason=AnalysisExitReason.SCHEMA_INCOMPATIBLE,
                error_message=str(exc),
                stderr_tail=str(exc)[-2000:],
            )
        except Exception as exc:
            diagnostic = str(exc)
            if run_started:
                try:
                    writer.finish_run(
                        RunMeta(
                            run_id=run_id,
                            branch=branch_name,
                            mode="rebuild" if rebuild else "incremental",
                            status="failed",
                            started_at=started_at,
                            finished_at=git.utc_now_epoch(),
                            commits_total=total,
                            commits_succeeded=succeeded,
                            commits_failed=failed,
                        )
                    )
                except Exception as finish_exc:
                    diagnostic = f"{diagnostic}; Failed to record terminal run state: {finish_exc}"
            return AnalysisRunResult(
                run_id=run_id,
                status=AnalysisTerminalState.FAILED,
                commits_total=total,
                commits_succeeded=succeeded,
                commits_failed=failed,
                mode=AnalysisEffectiveMode.REBUILD
                if rebuild
                else AnalysisEffectiveMode.INCREMENTAL,
                exit_reason=AnalysisExitReason.UNKNOWN,
                error_message=diagnostic,
                stderr_tail=diagnostic[-2000:],
            )
        finally:
            writer.close()
            if worktree_owned:
                cleanup_worktree(self._project_path, self._analysis_path)
