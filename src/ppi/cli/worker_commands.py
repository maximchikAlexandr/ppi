from __future__ import annotations

import asyncio
import json

import click

from ppi.worker_ipc.client import WorkerClientError


def cmd_run(ctx: dict) -> None:
    from ppi.worker_ipc.cli_handlers import run_worker_foreground
    run_worker_foreground(ctx)


def cmd_start(workspace_id: str, analysis_dir, repo, profile, json_output: bool) -> None:
    from ppi.worker_ipc.gateway import WorkerGateway
    from ppi.worker_ipc.runtime_paths import endpoint_for_workspace
    gateway = WorkerGateway(repo, profile, analysis_dir)
    client, diag = asyncio.run(gateway.get_client(start_if_missing=True))
    if diag["status"] == "healthy":
        data = {
            "ok": True,
            "workspace_id": workspace_id,
            "worker_id": diag.get("worker_id") or "",
            "state": "idle",
            "endpoint": endpoint_for_workspace(workspace_id).uri(),
            "protocol_version": "1.0",
        }
        if json_output:
            click.echo(json.dumps(data, indent=2))
        else:
            click.echo(f"Worker started: {diag.get('worker_id') or 'unknown'}")
    else:
        msg = f"Worker start failed: {diag['message']}"
        if json_output:
            click.echo(json.dumps({"ok": False, "error": msg}, indent=2))
        else:
            raise click.ClickException(msg)


def cmd_status(repo, profile, analysis_dir, json_output: bool) -> None:
    from ppi.worker_ipc.gateway import WorkerGateway
    gateway = WorkerGateway(repo, profile, analysis_dir)
    client, diag = asyncio.run(gateway.get_client(start_if_missing=False))
    if diag["status"] == "healthy" and client is not None:
        asyncio.run(client.close())
    data = {
        "status": diag["status"],
        "message": diag["message"],
        "details": diag.get("details"),
    }
    if json_output:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Worker status: {diag['status']}")


def cmd_stop(workspace_id, repo, profile, analysis_dir, json_output: bool) -> None:
    from ppi.worker_ipc.gateway import WorkerGateway
    from ppi.worker_ipc.runtime_metadata import read_metadata
    from ppi.worker_ipc.runtime_paths import metadata_path
    meta = read_metadata(metadata_path(workspace_id))
    if meta is None:
        if json_output:
            click.echo(json.dumps({"ok": True, "message": "No active worker"}))
        else:
            click.echo("No active worker.")
        return
    gateway = WorkerGateway(repo, profile, analysis_dir)
    client, diag = asyncio.run(gateway.get_client(start_if_missing=False))
    if diag["status"] != "healthy":
        if json_output:
            click.echo(json.dumps({"ok": True, "message": "No active worker"}))
        else:
            click.echo("No active worker.")
        return
    try:
        resp = asyncio.run(client.shutdown())
        if json_output:
            click.echo(json.dumps({"ok": True, "message": resp.get("message", "Shutdown accepted")}))
        else:
            click.echo(f"Worker stopped: {resp.get('message', 'Shutdown accepted')}")
    except WorkerClientError as exc:
        if json_output:
            click.echo(json.dumps({"ok": False, "error": exc.error.message}))
        else:
            raise click.ClickException(exc.error.message) from exc
    finally:
        if client is not None:
            asyncio.run(client.close())
