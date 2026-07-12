"""Machine-readable progress events for ``ppi analyze --json``.

Events are emitted as newline-delimited JSON on stdout. The event union is a
msgspec tagged union keyed by the ``type`` field, so consumers can discriminate
variants. The stream is strictly ordered::

    run_started -> commit_progress* -> (run_completed | run_failed)

Exactly one terminal event is emitted per run; if the process exits without a
terminal event, the caller MUST treat it as an unknown failure.
"""

from __future__ import annotations

import sys
import typing

import msgspec

__all__ = [
    "CommitProgress",
    "ProgressEvent",
    "RunCompleted",
    "RunFailed",
    "RunStarted",
    "decode_line",
    "emit",
]


class RunStarted(msgspec.Struct, frozen=True, tag="run_started"):
    """Emitted once when the analysis run begins."""

    run_id: str
    branch: str
    mode: typing.Literal["incremental", "rebuild"]
    commits_total: int


class CommitProgress(msgspec.Struct, frozen=True, tag="commit_progress"):
    """Emitted once per processed commit."""

    processed: int
    commits_total: int
    short_hash: str


class RunCompleted(msgspec.Struct, frozen=True, tag="run_completed"):
    """Terminal success event; replaces the human-readable summary line."""

    run_id: str
    commits_succeeded: int
    commits_failed: int
    duration_ms: int


class RunFailed(msgspec.Struct, frozen=True, tag="run_failed"):
    """Terminal failure event with a diagnostic tail for the caller."""

    run_id: str
    exit_reason: str
    message: str
    stderr_tail: str = ""


# Plain tagged union: each struct carries its own ``tag`` so msgspec can
# discriminate variants when decoding a ``ProgressEvent``.
ProgressEvent = RunStarted | CommitProgress | RunCompleted | RunFailed

_ENCODER = msgspec.json.Encoder()
_DECODER = msgspec.json.Decoder(ProgressEvent)


def emit(event: ProgressEvent, *, stream: typing.TextIO | None = None) -> None:
    out = stream if stream is not None else sys.stdout
    out.write(_ENCODER.encode(event).decode("utf-8"))
    out.write("\n")
    out.flush()


def decode_line(line: str) -> ProgressEvent:
    return typing.cast("ProgressEvent", _DECODER.decode(line.encode("utf-8")))
