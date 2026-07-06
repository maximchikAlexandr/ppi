"""Architecture boundary guardrails for spec 009.

Uses ast to inspect imports. Each rule prevents accidental coupling
between layers that must remain independent.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

WORKER_IPC = Path("src/ppi/worker_ipc")
PROTOCOL = WORKER_IPC / "protocol.py"
FRAMING = WORKER_IPC / "framing.py"
CLIENT = WORKER_IPC / "client.py"
QUERY_SERVICE = WORKER_IPC / "query_service.py"
WORKER_API = Path("src/ppi/server/worker_api.py")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_protocol_imports_only_stdlib_typing_enum_date_and_msgspec() -> None:
    modules = imported_modules(PROTOCOL)
    forbidden = {m for m in modules if m.startswith("ppi.") and not m.startswith("ppi.worker_ipc")}
    assert not forbidden, f"protocol.py must not import external ppi.*, found: {forbidden}"
    assert "msgspec" in modules


def test_framing_imports_only_stdlib_asyncio_struct_and_constants() -> None:
    modules = imported_modules(FRAMING)
    forbidden = {m for m in modules if m.startswith("ppi.") and not m.startswith("ppi.worker_ipc")}
    assert not forbidden, f"framing.py must not import external ppi.*, found: {forbidden}"


def test_client_does_not_import_click_fastapi_duckdb_writer_uvicorn() -> None:
    modules = imported_modules(CLIENT)
    forbidden = {"click", "fastapi", "duckdb", "uvicorn"}
    assert not (modules & forbidden), f"client.py must not import {modules & forbidden}"
    for mod in modules:
        assert "StoreWriter" not in mod, f"client.py must not import {mod}"


def test_worker_api_does_not_import_store_writer() -> None:
    source = WORKER_API.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "StoreWriter" not in alias.name, f"worker_api.py imports {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "StoreWriter" not in node.module, f"worker_api.py imports {node.module}"


def test_query_service_does_not_import_fastapi_or_click() -> None:
    modules = imported_modules(QUERY_SERVICE)
    forbidden = {"click", "fastapi"}
    assert not (modules & forbidden), f"query_service.py must not import {modules & forbidden}"


def test_protocol_imports_no_ppi_modules_outside_package() -> None:
    modules = imported_modules(PROTOCOL)
    forbidden = {m for m in modules if m.startswith("ppi.") and not m.startswith("ppi.worker_ipc")}
    assert not forbidden, f"protocol.py must not import external ppi.*, found: {forbidden}"


@pytest.mark.parametrize(
    "path",
    [
        WORKER_IPC / "protocol.py",
        WORKER_IPC / "framing.py",
        WORKER_IPC / "constants.py",
    ],
)
def test_typed_files_have_no_runtime_imports_of_app_layers(path: Path) -> None:
    modules = imported_modules(path)
    forbidden = {m for m in modules if m.startswith("ppi.server") or m.startswith("ppi.cli") or m.startswith("ppi.storage")}
    assert not forbidden, f"{path.name} must not import {forbidden}"


def test_ide_contract_module_defined() -> None:
    ide = WORKER_IPC / "ide_contract.py"
    if not ide.exists():
        pytest.skip("ide_contract.py not yet created")
    source = ide.read_text()
    assert "SUPPORTED_IDE_WORKER_COMMANDS" in source
