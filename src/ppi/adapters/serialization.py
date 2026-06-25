"""JSON serialization adapter for analysis batches (PPI-016).

Moves msgspec encoder/decoder out of :mod:`ppi.core.contracts` so contracts.py
stays a pure schema/value-contract layer that does not know about the JSON
transport. Runtime decode failures surface as a typed :class:`SerializationError`
instead of a bare msgspec exception.

The legacy ``ppi.core.contracts.batch_to_json`` / ``batch_from_json`` names are
re-exported here; callers can migrate at their own pace.
"""

from __future__ import annotations

import msgspec

from ppi.core.contracts import AnalysisBatch

__all__ = [
    "SerializationError",
    "batch_to_json",
    "batch_from_json",
    "encode_batch",
    "decode_batch",
]


class SerializationError(Exception):
    """Typed error raised when JSON encode/decode of a batch fails."""


_ENCODER = msgspec.json.Encoder()
_DECODER = msgspec.json.Decoder(AnalysisBatch)


def encode_batch(batch: AnalysisBatch) -> str:
    """Serialize one analysis batch to a JSON line."""
    try:
        return _ENCODER.encode(batch).decode("utf-8")
    except (msgspec.MsgspecError, UnicodeDecodeError) as exc:
        raise SerializationError(f"Failed to encode analysis batch: {exc}") from exc


def decode_batch(line: str) -> AnalysisBatch:
    """Deserialize one analysis batch from a JSON line."""
    try:
        return _DECODER.decode(line.encode("utf-8"))
    except (msgspec.MsgspecError, UnicodeDecodeError) as exc:
        raise SerializationError(f"Failed to decode analysis batch: {exc}") from exc


# Legacy-compatible names so callers can import from either module.
batch_to_json = encode_batch
batch_from_json = decode_batch
