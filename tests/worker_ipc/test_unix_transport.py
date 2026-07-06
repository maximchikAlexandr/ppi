"""Tests for unix_transport module."""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest

from ppi.worker_ipc.unix_transport import UnixClientTransport, UnixServerTransport

_SHORT_DIR = "/tmp/ppi-ut"


def _sock(name: str) -> Path:
    d = Path(_SHORT_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{name[0]}-{uuid.uuid4().hex[:6]}.sock"


async def _echo_byte_handler(payload: bytes) -> bytes:
    return b"echo:" + payload


async def _noop_byte_handler(payload: bytes) -> bytes:
    return b""


@pytest.mark.asyncio
async def test_unix_client_transport_request_bytes_roundtrip() -> None:
    path = _sock("c")
    server = UnixServerTransport(path, _echo_byte_handler)
    await server.start()
    try:
        client = UnixClientTransport(path)
        await client.connect()
        resp = await client.request_bytes(b"hello")
        assert resp == b"echo:hello"
        await client.close()
    finally:
        await server.stop()
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@pytest.mark.asyncio
async def test_unix_client_transport_request_bytes_large() -> None:
    path = _sock("b")
    payload = b"x" * 1024

    async def passthrough(p: bytes) -> bytes:
        return p

    server = UnixServerTransport(path, passthrough)
    await server.start()
    try:
        client = UnixClientTransport(path)
        await client.connect()
        resp = await client.request_bytes(payload)
        assert resp == payload
        await client.close()
    finally:
        await server.stop()
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@pytest.mark.asyncio
async def test_unix_server_transport_starts_and_stops() -> None:
    path = _sock("s")
    server = UnixServerTransport(path, _noop_byte_handler)
    await server.start()
    assert path.exists()
    await server.stop()
    try:
        path.unlink()
    except FileNotFoundError:
        pass


@pytest.mark.asyncio
async def test_unix_client_transport_close() -> None:
    path = _sock("x")
    server = UnixServerTransport(path, _noop_byte_handler)
    await server.start()
    try:
        client = UnixClientTransport(path)
        await client.connect()
        await client.close()
    finally:
        await server.stop()
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@pytest.mark.asyncio
async def test_unix_client_transport_connect_fails_no_server(tmp_path: Path) -> None:
    path = tmp_path / "no-server.sock"
    client = UnixClientTransport(path)
    with pytest.raises(Exception):
        await client.connect()


@pytest.mark.asyncio
async def test_unix_server_transport_refuses_existing_socket() -> None:
    """When a socket already exists, server.start(force=False) refuses."""
    path = _sock("r")
    server1 = UnixServerTransport(path, _noop_byte_handler)
    await server1.start(force=True)
    try:
        server2 = UnixServerTransport(path, _noop_byte_handler)
        with pytest.raises(FileExistsError):
            await server2.start(force=False)
    finally:
        await server1.stop()
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@pytest.mark.asyncio
async def test_unix_server_transport_force_replaces_existing() -> None:
    """When force=True, server.start() unlinks and rebinds."""
    path = _sock("f")
    server1 = UnixServerTransport(path, _noop_byte_handler)
    await server1.start(force=True)
    await server1.stop()
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    server2 = UnixServerTransport(path, _noop_byte_handler)
    await server2.start(force=True)
    try:
        assert path.exists()
    finally:
        await server2.stop()
        try:
            path.unlink()
        except FileNotFoundError:
            pass
