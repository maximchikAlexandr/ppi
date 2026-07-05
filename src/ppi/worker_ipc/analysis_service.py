from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path

from ppi.core.odoo.pipeline import build_report_config
from ppi.core.contracts import ProjectRef, RunMeta
from ppi.history import git
from ppi.history.walker import walk_history
from ppi.runtime import lock as project_lock
from ppi.runtime.paths import (
    project_id_from_repo,
    writer_lock_path,
)
from ppi.storage.writer import StoreWriter


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

    async def run(
        self,
        mode: str = "incremental",
        cancel_flag: Callable[[], bool] | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> None:
        rebuild = mode == "full"
        run_id = str(uuid.uuid4())
        started_at = git.utc_now_epoch()
        branch_result = git.resolve_branch(self._project_path, None)
        project_id = project_id_from_repo(self._project_path)
        branch_name = branch_result.ok if branch_result.is_ok() else "unknown"

        writer: StoreWriter | None = None
        try:
            writer = StoreWriter(self._store_path)

            if rebuild:
                writer.clear_project_data()

            report_config = build_report_config(
                project_label=self._project_path.name,
                module_prefixes=(),
                include_modules=(),
                all_modules=True,
            )
            skip_commits: set[str] = set()
            if not rebuild:
                stored = writer.get_project()
                if stored is not None:
                    if stored.project_id != project_id:
                        raise RuntimeError("Repository changed; rerun with --rebuild")
                    if stored.branch != branch_name:
                        raise RuntimeError("Branch changed; rerun with --rebuild")
                skip_commits = writer.stored_commit_hashes()

            writer.upsert_project(ProjectRef(
                project_id=project_id,
                repo_path=str(self._project_path),
                branch=branch_name,
                profile=self._profile,
            ))

            writer.start_run(RunMeta(
                run_id=run_id,
                branch=branch_name,
                mode="rebuild" if rebuild else "incremental",
                status="running",
                started_at=started_at,
                finished_at=None,
                commits_total=0,
                commits_succeeded=0,
                commits_failed=0,
            ))

            lock_file = writer_lock_path(self._project_path)
            with project_lock.write_lock(lock_file):
                prepared = walk_history(
                    self._project_path,
                    branch_name,
                    self._analysis_path,
                    profile=self._profile,
                    skip_commits=skip_commits,
                    addons_paths=(),
                    report_config=report_config,
                )
                if prepared.is_error():
                    raise RuntimeError(prepared.error)

                batches, state = prepared.ok
                total = state.commits_total if state else 0
                processed = 0

                for batch in batches:
                    if cancel_flag is not None and cancel_flag():
                        writer.finish_run(RunMeta(
                            run_id=run_id,
                            branch=branch_name,
                            mode="rebuild" if rebuild else "incremental",
                            status="cancelled",
                            started_at=started_at,
                            finished_at=git.utc_now_epoch(),
                            commits_total=total,
                            commits_succeeded=processed,
                            commits_failed=0,
                        ))
                        return

                    writer.write_batch(batch, run_id)
                    processed += 1
                    if progress_callback is not None and total > 0:
                        pct = (processed / total) * 100.0
                        progress_callback(pct, f"Analyzed {processed}/{total} commits")

                writer.finish_run(RunMeta(
                    run_id=run_id,
                    branch=branch_name,
                    mode="rebuild" if rebuild else "incremental",
                    status="completed",
                    started_at=started_at,
                    finished_at=git.utc_now_epoch(),
                    commits_total=total,
                    commits_succeeded=processed,
                    commits_failed=0,
                ))
        finally:
            if writer is not None:
                writer.close()
