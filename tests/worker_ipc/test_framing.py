import asyncio
import struct
from unittest.mock import MagicMock

import pytest

from ppi.worker_ipc.constants import MAX_FRAME_BYTES
from ppi.worker_ipc.framing import read_frame, write_frame


def _reader_from_bytes(data: bytes) -> asyncio.StreamReader:
    reader = asyncio.StreamReader()
    reader.feed_data(data)
    return reader


def _make_writer() -> tuple[MagicMock, bytearray]:
    written = bytearray()

    def _write(data: bytes) -> None:
        written.extend(data)

    transport = MagicMock()
    transport.write = _write
    writer = asyncio.StreamWriter(transport, asyncio.Protocol(), None, asyncio.get_event_loop())
    return writer, written


@pytest.mark.asyncio
async def test_one_frame_encode_decode() -> None:
    payload = b"hello world"
    writer, written = _make_writer()
    write_frame(writer, payload)

    reader = _reader_from_bytes(bytes(written))
    result = await read_frame(reader)
    assert result == payload


@pytest.mark.asyncio
async def test_multiple_frames() -> None:
    payloads = [b"frame1", b"frame2", b"frame3"]
    writer, written = _make_writer()
    for p in payloads:
        write_frame(writer, p)

    reader = _reader_from_bytes(bytes(written))
    for expected in payloads:
        result = await read_frame(reader)
        assert result == expected


@pytest.mark.asyncio
async def test_frame_too_large() -> None:
    reader = _reader_from_bytes(struct.pack("!I", MAX_FRAME_BYTES + 1))
    with pytest.raises(ValueError, match="Frame payload"):
        await read_frame(reader)


@pytest.mark.asyncio
async def test_incomplete_payload() -> None:
    reader = _reader_from_bytes(struct.pack("!I", 100) + b"short")
    reader.feed_eof()
    with pytest.raises(ConnectionError, match="Stream ended"):
        await read_frame(reader)
