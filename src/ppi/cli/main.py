"""CLI entry point for ppi."""

from __future__ import annotations

import asyncio
import csv
import io
import json
import socket
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click

from ppi.core.contracts import ProjectRef
from ppi.history import git
from ppi.history.worktree import remove_worktree
from ppi.query.rpc_server import serve_rpc
from ppi.runtime import lock as project_lock
from ppi.runtime.log import get_logger, set_verbose
from ppi.runtime.names import parse_module_file_path
from ppi.runtime.paths import (
    analysis_dir_for_repo,
    assert_outside_repo,
    ensure_analysis_dir,
    ensure_in_project_store,
    in_project_store_dir,
    lock_path,
    project_id_from_repo,
    store_path,
    worktree_path,
    writer_lock_path,
)
from ppi.runtime.progress import CommitProgress, RunCompleted, RunFailed, RunStarted, emit
from ppi.storage import schema
from ppi.worker_ipc.client import WorkerClientError
from ppi.worker_ipc.gateway import WorkerGateway
from ppi.worker_ipc.protocol import AnalysisRequestMode, AnalysisStartRequest, WorkerEventType

log = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class CliContext:
    """Shared CLI configuration."""

    repo: Path
    branch: str | None
    profile: str
    analysis_dir: Path
    verbose: bool = False


pass_context = click.make_pass_decorator(CliContext, ensure=True)


def _parse_file_path(file_path: str) -> tuple[str, str]:
    """Split a CLI file filter into module name and relative path."""
    try:
        return parse_module_file_path(file_path)
    except ValueError as exc:
        raise click.ClickException("--file must be module/relative/path") from exc


async def _analyze_via_worker(
    client: Any,
    request: AnalysisStartRequest,
    json_output: bool,
    store_file: Path | None = None,
) -> None:
    events: asyncio.Queue[Any] = asyncio.Queue()
    stream_ready = asyncio.Event()
    supports_handshake = False

    async def _follow_events() -> None:
        async for event in client.events_stream(
            [WorkerEventType.ANALYSIS_PROGRESS, WorkerEventType.ANALYSIS_FAILED],
            ready=stream_ready if supports_handshake else None,
        ):
            await events.put(event)

    follower: asyncio.Task[None] | None = None
    emitted_started = False

    def _emit_started(commits_total: int, status: dict[str, Any] | None = None) -> None:
        nonlocal emitted_started
        if not emitted_started:
            source = status or {}
            emit(RunStarted(
                run_id=run_id,
                branch=source.get("branch") or request.branch,
                mode=source.get("mode") or ("rebuild" if request.mode == "full" else "incremental"),
                commits_total=commits_total,
            ))
            emitted_started = True

    def _emit_progress() -> None:
        while not events.empty():
            event = events.get_nowait()
            if event.event_type != WorkerEventType.ANALYSIS_PROGRESS:
                continue
            payload = event.payload
            _emit_started(int(payload["commits_total"]), payload)
            emit(CommitProgress(
                processed=int(payload["processed"]),
                commits_total=int(payload["commits_total"]),
                short_hash=str(payload["short_hash"]),
            ))

    try:
        try:
            if json_output:
                health = await client.health()
                supports_handshake = bool(health.get("events_stream_ready_handshake", False))
                follower = asyncio.create_task(_follow_events())
            if supports_handshake:
                await asyncio.wait_for(stream_ready.wait(), timeout=5.0)
            resp = await client.analysis_start(request)
        except WorkerClientError as exc:
            raise click.ClickException(exc.error.message) from exc
        state = resp.get("state", "running")
        run_id = resp.get("run_id", "unknown")
        if not json_output:
            click.echo(f"Analysis {state} (run_id: {run_id})")
            if state == "already_running":
                click.echo("Analysis is already running; following existing run.")
        last_msg = ""
        for _ in range(600):
            status = await client.analysis_status()
            state = status.get("state", "")
            if state in ("completed", "failed", "cancelled"):
                message = status.get("message", f"Analysis {state}")
                if json_output:
                    await asyncio.sleep(0)
                    _emit_progress()
                    total = status.get("commits_total", 0)
                    succeeded = status.get("commits_succeeded", 0)
                    failed = status.get("commits_failed", 0)
                    _emit_started(total, status)
                    if state == "completed":
                        emit(RunCompleted(run_id=run_id, commits_succeeded=succeeded,
                                          commits_failed=failed, duration_ms=0))
                    else:
                        emit(RunFailed(
                            run_id=run_id,
                            exit_reason=status.get("exit_reason") or "unknown",
                            message=message,
                            stderr_tail=status.get("stderr_tail") or message,
                        ))
                else:
                    click.echo(message)
                    if state == "completed":
                        click.echo(f"Store: {store_file}" if store_file else "Store updated")
                if state != "completed":
                    raise click.ClickException(message)
                return
            msg = status.get("message", "")
            if json_output:
                _emit_progress()
            if msg != last_msg:
                if not json_output:
                    click.echo(f"  progress: {status.get('progress_percent', '?')}% — {msg}")
                last_msg = msg
            await asyncio.sleep(1)
        raise click.ClickException("Timed out waiting for analysis worker")
    finally:
        if follower is not None:
            follower.cancel()
            try:
                await follower
            except asyncio.CancelledError:
                pass
        await client.close()


def _emit_query_rows(rows: list[dict], output_format: str) -> None:
    """Print query result rows in the selected output format."""
    if output_format == "json":
        click.echo(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
        return
    if not rows:
        click.echo("No rows.")
        return
    if output_format == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        click.echo(buffer.getvalue().rstrip("\n"))
        return
    headers = list(rows[0].keys())
    click.echo(" | ".join(headers))
    for row in rows:
        click.echo(" | ".join(str(row[key]) for key in headers))


def _recover_stale_artifacts(ctx: CliContext) -> list[str]:
    """Remove stale worktree and orphan lock files when safe."""
    actions: list[str] = []
    locked = project_lock.is_locked(writer_lock_path(ctx.repo))
    wt = worktree_path(ctx.analysis_dir)
    if wt.exists() and not locked:
        removed = remove_worktree(ctx.repo, ctx.analysis_dir)
        if removed.is_ok():
            actions.append("removed stale worktree")
    lock_file = writer_lock_path(ctx.repo)
    if lock_file.is_file() and not project_lock.is_locked(lock_file):
        lock_file.unlink(missing_ok=True)
        actions.append("removed stale lock file")
    return actions


def _assert_store_metadata(ctx: CliContext, stored: ProjectRef) -> None:
    """Ensure CLI branch and profile match the store."""
    branch_result = git.resolve_branch(ctx.repo, ctx.branch)
    if branch_result.is_error():
        raise click.ClickException(branch_result.error)
    if stored.branch != branch_result.ok:
        raise click.ClickException(
            f"Store contains branch {stored.branch!r}; rerun analyze for {branch_result.ok!r}.",
        )
    if stored.profile != ctx.profile:
        raise click.ClickException(
            f"Store contains profile {stored.profile!r}; "
            f"rerun analyze with profile {ctx.profile!r}.",
        )


def _resolve_context(
    repo: Path,
    branch: str | None,
    profile: str,
    analysis_dir: Path | None,
) -> CliContext:
    """Build shared CLI context and validate artifact placement."""
    if profile != "odoo":
        raise click.ClickException(f"Unsupported analysis profile: {profile}")
    resolved_repo = repo.resolve()
    analysis = analysis_dir or analysis_dir_for_repo(resolved_repo)
    try:
        ensure_analysis_dir(analysis)
        ensure_in_project_store(resolved_repo)
        for artifact in (analysis, worktree_path(analysis), lock_path(analysis)):
            assert_outside_repo(resolved_repo, artifact)
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    return CliContext(
        repo=resolved_repo,
        branch=branch,
        profile=profile,
        analysis_dir=analysis,
    )


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--repo", type=click.Path(exists=True, file_okay=False, path_type=Path), required=True
)
@click.option("--branch", default=None, help="Branch to analyze; defaults to current branch.")
@click.option("--profile", default="odoo", show_default=True)
@click.option(
    "--analysis-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Directory for store, worktree, and runtime artifacts.",
)
@click.option("-v", "--verbose", is_flag=True, help="Extra diagnostics on stderr.")
@click.pass_context
def cli(
    click_ctx: click.Context,
    repo: Path,
    branch: str | None,
    profile: str,
    analysis_dir: Path | None,
    verbose: bool,
) -> None:
    """Analyze Git history metrics for Python/Odoo projects.

    Analyze always uses the workspace worker; query can opt in with --via-worker.
    See 'worker start', 'worker status', and 'worker stop' for lifecycle commands.
    """
    set_verbose(verbose)
    base = _resolve_context(repo, branch, profile, analysis_dir)
    click_ctx.obj = CliContext(
        repo=base.repo,
        branch=base.branch,
        profile=base.profile,
        analysis_dir=base.analysis_dir,
        verbose=verbose,
    )


@cli.command()
@click.option("--rebuild", is_flag=True, help="Drop stored history and re-analyze all commits.")
@click.option(
    "--jsonl",
    "jsonl_output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSONL output path for analysis batches.",
)
@click.option(
    "--addons-path",
    "addons_paths",
    multiple=True,
    help=(
        "Relative addons root inside the worktree; repeat for multiple roots. "
        "Defaults to worktree root."
    ),
)
@click.option(
    "--module-prefix", "module_prefixes", multiple=True, help="Include modules with this prefix."
)
@click.option(
    "--include-module", "include_modules", multiple=True, help="Include exact module names."
)
@click.option("--all-modules", "all_modules", is_flag=True, help="Include every discovered module.")
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Emit machine-readable JSON-lines progress events on stdout and suppress human output.",
)
@click.option(
    "--via-worker",
    is_flag=True,
    help="Retained for compatibility; analyze always uses the workspace worker.",
)
@pass_context
def analyze(
    ctx: CliContext,
    rebuild: bool,
    jsonl_output: Path | None,
    addons_paths: tuple[str, ...],
    module_prefixes: tuple[str, ...],
    include_modules: tuple[str, ...],
    all_modules: bool,
    json_output: bool,
    via_worker: bool,
) -> None:
    """Walk non-merge commit history and collect metrics."""
    branch_result = git.resolve_branch(ctx.repo, ctx.branch)
    if branch_result.is_error():
        message = str(branch_result.error)
        if json_output:
            emit(RunFailed(
                run_id="unstarted",
                exit_reason="bad_workspace",
                message=message,
                stderr_tail=message,
            ))
        raise click.ClickException(message)

    gateway = WorkerGateway(ctx.repo, ctx.profile, ctx.analysis_dir)
    request = AnalysisStartRequest(
        mode=AnalysisRequestMode.FULL if rebuild else AnalysisRequestMode.INCREMENTAL,
        reason="cli",
        branch=branch_result.ok,
        jsonl_output=str(jsonl_output) if jsonl_output else None,
        addons_paths=tuple(addons_paths),
        module_prefixes=tuple(module_prefixes),
        include_modules=tuple(include_modules),
        all_modules=all_modules or (not module_prefixes and not include_modules),
    )

    async def _run_worker_analysis() -> None:
        result = await gateway.get_client(start_if_missing=True)
        if result is None or result.status != "healthy":
            raise click.ClickException("Failed to start or attach worker")
        await _analyze_via_worker(
            result.client, request, json_output,
            store_file=store_path(ctx.repo),
        )

    asyncio.run(_run_worker_analysis())


def _verify_store_schema(store_file: Path) -> None:
    """Verify store schema compatibility, raising ClickException on mismatch."""
    import duckdb
    try:
        conn = duckdb.connect(str(store_file), read_only=True)
        try:
            schema.assert_schema_compatible(conn)
        finally:
            conn.close()
    except schema.SchemaIncompatibleError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:
        raise click.ClickException(f"Store error: {exc}") from exc


def _query_dispatch(
    store_file: Path, method: str, params: dict,
) -> dict | list:
    """Run one read query via the Ibis pipeline and return the payload."""
    from expression.core.result import Result

    from ppi.query import dispatch as qdispatch
    result = qdispatch(store_file, method, params, writer_active=False, store_present=True)
    match result:
        case Result(tag='ok', ok=value):
            return value
        case Result(tag='error', error=err):
            raise click.ClickException(err.message) from None


_METRIC_TO_METHOD = {
    "graph": "graph",
    "snapshot-table-modules": "snapshot/table/modules",
    "snapshot-table-files": "snapshot/table/files",
    "snapshot-relations": "snapshot/relations",
    "project-info": "project/info",
    "ui-config": "ui/config",
}


def _cli_metric_to_method(metric: str) -> str:
    return _METRIC_TO_METHOD.get(metric, "metrics/timeseries")


@cli.command()
@click.option("--metric", type=str, required=True)
@click.option("--module", "module_name", default=None)
@click.option(
    "--file", "file_path", default=None, help="Filter to one file as module/relative/path."
)
@click.option("--commit", "commit_hash", default=None, help="Snapshot selector (default: latest).")
@click.option(
    "--agg",
    type=click.Choice(["mean", "median", "p95", "max"], case_sensitive=False),
    default="mean",
    show_default=True,
)
@click.option(
    "--include-zero-score", is_flag=True, help="Include score==0 edges in graph/edge reads."
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"], case_sensitive=False),
    default="table",
    show_default=True,
)
@click.option(
    "--via-worker",
    is_flag=True,
    help="Route this command through the workspace worker IPC boundary.",
)
@pass_context
def query(
    ctx: CliContext,
    metric: str,
    module_name: str | None,
    file_path: str | None,
    commit_hash: str | None,
    agg: str,
    include_zero_score: bool,
    output_format: str,
    via_worker: bool,
) -> None:
    """Query stored metrics without re-running analysis (Ibis pipeline)."""
    if via_worker:
        import asyncio

        from ppi.worker_ipc.client import WorkerClientError
        from ppi.worker_ipc.gateway import WorkerGateway
        gateway = WorkerGateway(ctx.repo, ctx.profile, ctx.analysis_dir)
        result = asyncio.run(gateway.get_client(start_if_missing=False))
        if result is None or result.status != "healthy":
            raise click.ClickException("Worker not available. Use 'worker start' first or omit --via-worker for direct query.")
        client = result.client
        query_name = _cli_metric_to_method(metric)
        if query_name == "metrics/timeseries":
            if not file_path and not module_name:
                raise click.ClickException("--module or --file required for metric timeseries")
            params = {"level": "file" if file_path else "module", "metric_id": metric, "name": file_path or module_name, "agg": agg}
        else:
            params = {"commit": commit_hash, "include_zero_score": include_zero_score}
        try:
            resp = asyncio.run(client.query_execute(query_name=query_name, parameters=params))
        except WorkerClientError as exc:
            raise click.ClickException(exc.error.message) from exc
        if resp.get("error_code"):
            raise click.ClickException(f"Query failed: {resp.get('message', 'unknown error')}")
        click.echo(json.dumps(resp, ensure_ascii=False, indent=2, default=str))
        asyncio.run(client.close())
        return
    metric = metric.lower()
    if module_name and file_path:
        raise click.ClickException("Use either --module or --file, not both.")
    if project_lock.is_locked(writer_lock_path(ctx.repo)):
        raise click.ClickException("Analysis in progress; query later.")
    store_file = store_path(ctx.repo)
    if not store_file.is_file():
        raise click.ClickException("Store not found. Run 'ppi analyze' first.")
    method = _cli_metric_to_method(metric)
    if method == "metrics/timeseries":
        if file_path:
            name = file_path
        elif module_name:
            name = module_name
        else:
            raise click.ClickException("--module or --file required for metric timeseries")
        params = {"level": "file" if file_path else "module", "metric_id": metric, "name": name, "agg": agg}
    else:
        params = {"commit": commit_hash, "include_zero_score": include_zero_score}
    payload = _query_dispatch(store_file, method, params)
    if isinstance(payload, dict):
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    _emit_query_rows(payload, output_format)


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8765, show_default=True, type=int)
@click.option("--open", "open_browser", is_flag=True)
@click.option(
    "--via-worker",
    is_flag=True,
    help="Route through workspace worker IPC boundary.",
)
@pass_context
def serve(ctx: CliContext, host: str, port: int, open_browser: bool, via_worker: bool) -> None:
    """Start the dashboard API server."""
    import asyncio
    store_file = store_path(ctx.repo)
    if store_file.is_file():
        _verify_store_schema(store_file)

    worker_client = None
    if via_worker:
        from ppi.worker_ipc.gateway import WorkerGateway
        gateway = WorkerGateway(ctx.repo, ctx.profile, ctx.analysis_dir)
        result = asyncio.run(gateway.get_client(start_if_missing=True))
        if result is not None and result.status == "healthy":
            worker_client = result.client
            log.info("Worker attached: %s", result.worker_id)

    import uvicorn

    from ppi.server.app import STATIC_DIR, _static_dir, create_app

    static_dir = _static_dir()
    if static_dir == STATIC_DIR:
        log.warning(
            "frontend/dist not found; serving fallback static UI. "
            "Build the dashboard: cd frontend && npm install && npm run build",
        )
    app = create_app(store_path(ctx.repo), writer_lock_path(ctx.repo), worker_client=worker_client)
    url = f"http://{host}:{port}/"
    if open_browser:
        webbrowser.open(url)
    try:
        uvicorn.run(app, host=host, port=port)
    finally:
        if worker_client is not None:
            asyncio.run(worker_client.close())


@cli.command()
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    default="-",
    show_default=True,
    help="Output path; '-' for stdout.",
)
@pass_context
def openapi(ctx: CliContext, output: str) -> None:
    """Export the dashboard API OpenAPI 3.1 schema as JSON.

    Used by downstream codegen (openapi-typescript, openapi-fetch) to
    replace manually-maintained frontend schemas with generated SDK.
    """
    import json as _json

    from ppi.server.app import openapi_schema

    schema = openapi_schema(store_path(ctx.repo), writer_lock_path(ctx.repo))
    serialized = _json.dumps(schema, indent=2, ensure_ascii=False)
    if output == "-":
        click.echo(serialized)
        return
    Path(output).write_text(serialized, encoding="utf-8")
    click.echo(f"WROTE {output}")


@cli.command()
@pass_context
def rpc(ctx: CliContext) -> None:
    """Run a long-lived read-only JSON-RPC query servant over stdio.

    The store and writer lock are resolved from ``repo`` (same as ``analyze``);
    ``--analysis-dir`` on the CLI group only affects the worktree used by
    ``analyze`` and is ignored here.
    """
    serve_rpc(ctx.repo)


@cli.command()
@click.option(
    "--recover-stale",
    is_flag=True,
    help="Remove stale worktree and orphan lock files when safe.",
)
@pass_context
def doctor(ctx: CliContext, recover_stale: bool) -> None:
    """Verify environment prerequisites."""
    if recover_stale:
        for action in _recover_stale_artifacts(ctx):
            click.echo(f"RECOVERED {action}")
    checks: list[tuple[str, bool, str]] = []
    git_check = git.git_version(ctx.repo)
    checks.append(
        ("git", git_check.is_ok(), git_check.ok.strip() if git_check.is_ok() else git_check.error)
    )
    branch_check = git.resolve_branch(ctx.repo, ctx.branch)
    checks.append(
        (
            "branch",
            branch_check.is_ok(),
            branch_check.ok if branch_check.is_ok() else branch_check.error,
        )
    )
    writable = False
    writable_message = ""
    try:
        test_file = ctx.analysis_dir / ".write_test"
        ctx.analysis_dir.mkdir(parents=True, exist_ok=True)
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        writable = True
        writable_message = str(ctx.analysis_dir)
    except OSError as exc:
        writable_message = str(exc)
    checks.append(("analysis_dir_writable", writable, writable_message))
    ppi_ok = True
    ppi_message = "not created yet"
    try:
        ensure_in_project_store(ctx.repo)
        ppi_message = str(in_project_store_dir(ctx.repo))
    except ValueError as exc:
        ppi_ok = False
        ppi_message = str(exc)
    checks.append(("ppi_dir", ppi_ok, ppi_message))
    tracked = subprocess.run(
        ["git", "-C", str(ctx.repo), "ls-files", "--error-unmatch", ".ppi"],
        capture_output=True,
        text=True,
    )
    if tracked.returncode == 0:
        click.echo(
            "WARN .ppi is tracked in git; self-ignoring .gitignore cannot untrack committed files"
        )
    store_ok = True
    store_message = "store not created yet"
    store_file = store_path(ctx.repo)
    if store_file.is_file():
        try:
            import duckdb
            conn = duckdb.connect(str(store_file), read_only=True)
            try:
                schema.assert_schema_compatible(conn)
            finally:
                conn.close()
            store_message = f"store readable (schema_version={schema.SCHEMA_VERSION})"
        except schema.SchemaIncompatibleError as exc:
            store_ok = False
            store_message = str(exc)
        except Exception as exc:  # noqa: BLE001
            store_ok = False
            store_message = str(exc)
    checks.append(("store", store_ok, store_message))
    locked = project_lock.is_locked(writer_lock_path(ctx.repo))
    checks.append(("writer_lock", not locked, "free" if not locked else "locked"))
    worktree_exists = worktree_path(ctx.analysis_dir).exists()
    checks.append(
        (
            "worktree",
            not worktree_exists,
            "absent" if not worktree_exists else "stale worktree present",
        )
    )

    registry_path = Path.home() / ".local" / "share" / "ppi" / "workspaces.json"
    registry_ok = True
    if not registry_path.parent.exists():
        try:
            registry_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            registry_ok = False
            registry_path = Path(str(exc))
    checks.append(
        ("worker_registry", registry_ok, str(registry_path))
    )
    from ppi.runtime.lock import is_locked as is_lock_locked
    from ppi.worker_ipc.runtime_paths import runtime_dir, startup_lock_path
    ws_id = project_id_from_repo(ctx.repo)
    runtime_dir_path = runtime_dir(ws_id)
    checks.append(
        ("worker_runtime_dir", True, str(runtime_dir_path))
    )
    from ppi.worker_ipc.runtime_metadata import read_metadata
    from ppi.worker_ipc.runtime_paths import metadata_path, socket_path
    meta_path = metadata_path(ws_id)
    sock = socket_path(ws_id)
    if not meta_path.is_file():
        checks.append(("worker_metadata", True, "unavailable"))
    else:
        meta = read_metadata(meta_path)
        if meta is None:
            checks.append(("worker_metadata", False, "corrupt"))
        elif meta.state == "stale":
            checks.append(("worker_metadata", True, "stale"))
        else:
            checks.append(("worker_metadata", True, f"healthy (pid={meta.pid})"))
    if not sock.exists():
        checks.append(("worker_socket", True, "missing"))
    else:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(str(sock))
            s.close()
            checks.append(("worker_socket", True, "reachable"))
        except OSError:
            checks.append(("worker_socket", False, "unreachable"))
    start_lock = startup_lock_path(ws_id)
    if not start_lock.exists():
        checks.append(("worker_startup_lock", True, "free"))
    elif is_lock_locked(start_lock):
        checks.append(("worker_startup_lock", False, "locked"))
    else:
        checks.append(("worker_startup_lock", True, "stale lock file present"))

    failed = False
    for name, ok, detail in checks:
        status = "OK" if ok else "FAIL"
        click.echo(f"{status} {name}: {detail}")
        failed = failed or not ok
    if not recover_stale and (locked or worktree_exists):
        click.echo(
            "Hint: rerun with --recover-stale to remove stale worktree or orphan lock files."
        )
    if not recover_stale:
        from ppi.worker_ipc.runtime_paths import metadata_path
        if metadata_path(project_id_from_repo(ctx.repo)).is_file():
            click.echo(
                "Info: Worker runtime metadata exists. Use 'worker status' to check worker state "
                "or 'doctor --recover-stale' to recover worker metadata."
            )
    if failed:
        sys.exit(1)


@cli.group()
@pass_context
def worker(ctx: CliContext) -> None:
    """Manage workspace worker processes."""


@worker.command(hidden=True)
@pass_context
def run(ctx: CliContext) -> None:
    """Run worker in foreground (internal)."""
    from ppi.cli.worker_commands import cmd_run
    workspace_id = project_id_from_repo(ctx.repo)
    cmd_run({
        "workspace_id": workspace_id,
        "project_path": str(ctx.repo),
        "analysis_path": str(ctx.analysis_dir),
        "profile": ctx.profile,
    })


@worker.command()
@click.option("--json", "json_output", is_flag=True, help="Output JSON.")
@pass_context
def start(ctx: CliContext, json_output: bool) -> None:
    """Start a workspace worker process."""
    from ppi.cli.worker_commands import cmd_start
    ws_id = project_id_from_repo(ctx.repo)
    cmd_start(ws_id, ctx.analysis_dir, ctx.repo, ctx.profile, json_output)


@worker.command()
@click.option("--json", "json_output", is_flag=True, help="Output JSON.")
@pass_context
def status(ctx: CliContext, json_output: bool) -> None:
    """Check worker status."""
    from ppi.cli.worker_commands import cmd_status
    cmd_status(ctx.repo, ctx.profile, ctx.analysis_dir, json_output)


@worker.command()
@click.option("--json", "json_output", is_flag=True, help="Output JSON.")
@pass_context
def stop(ctx: CliContext, json_output: bool) -> None:
    """Stop a workspace worker process."""
    from ppi.cli.worker_commands import cmd_stop
    ws_id = project_id_from_repo(ctx.repo)
    cmd_stop(ws_id, ctx.repo, ctx.profile, ctx.analysis_dir, json_output)


# Import and register the devtools CLI group (spec 011)
from ppi.devtools.cli import dev_group

cli.add_command(dev_group)

if __name__ == "__main__":
    cli()
