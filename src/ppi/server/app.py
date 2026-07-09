from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ppi.server import api, api_v1
from ppi.server import worker_api
from ppi.worker_ipc.client import WorkerClient

STATIC_DIR = Path(__file__).resolve().parent / "static"
FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"


def _static_dir() -> Path | None:
    if (FRONTEND_DIST / "index.html").is_file():
        return FRONTEND_DIST
    if STATIC_DIR.is_dir():
        return STATIC_DIR
    return None


def create_app(
    store_file: Path,
    lock_file: Path,
    worker_client: WorkerClient | None = None,
) -> FastAPI:
    app = FastAPI(title="Python Project Inspector")
    app.state.store_file = store_file
    app.state.lock_file = lock_file
    app.state.worker_client = worker_client
    app.include_router(api.router, prefix="/api")
    app.include_router(api_v1.router, prefix="/api/v1")
    api_v1.install_error_handlers(app)
    if worker_client is not None:
        app.include_router(worker_api.router)
    static_dir = _static_dir()
    if static_dir is not None:
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return app


def openapi_schema(store_file: Path, lock_file: Path, worker_client: WorkerClient | None = None) -> dict:
    return create_app(store_file, lock_file, worker_client=worker_client).openapi()
