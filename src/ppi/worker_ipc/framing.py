from __future__ import annotations

import asyncio
import struct

from ppi.worker_ipc.constants import MAX_FRAME_BYTES

_HEADER_FORMAT = "!I"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)


async def read_frame(reader: asyncio.StreamReader) -> bytes:
    try:
        header = await reader.readexactly(_HEADER_SIZE)
    except asyncio.IncompleteReadError as exc:
        raise ConnectionError(f"Incomplete frame header: {exc}") from exc
    (payload_length,) = struct.unpack(_HEADER_FORMAT, header)
    if payload_length > MAX_FRAME_BYTES:
        raise ValueError(
            f"Frame payload {payload_length} exceeds maximum {MAX_FRAME_BYTES}"
        )
    try:
        payload = await reader.readexactly(payload_length)
    except asyncio.IncompleteReadError:
        raise ConnectionError("Stream ended before frame payload was complete")
    return payload


def write_frame(writer: asyncio.StreamWriter, payload: bytes) -> None:
    length = len(payload)
    if length > MAX_FRAME_BYTES:
        raise ValueError(
            f"Frame payload {length} exceeds maximum {MAX_FRAME_BYTES}"
        )
    writer.write(struct.pack(_HEADER_FORMAT, length))
    writer.write(payload)
