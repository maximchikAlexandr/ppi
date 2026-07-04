"""Python ROP pipeline stage types and result aliases.

Wraps ``Expression`` primitives into PPI-specific stage vocabulary.
All covered pipeline stages use these aliases so the domain speaks a
consistent ROP language.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from expression.core.result import Result as _ExprResult

from ppi.rop.errors import TypedStageError

StageResult = _ExprResult

I = TypeVar("I")
O = TypeVar("O")

PipelineStage = Callable[[I], StageResult[O, TypedStageError]]
AsyncPipelineStage = Callable[[I], Awaitable[StageResult[O, TypedStageError]]]

__all__ = [
    "StageResult",
    "PipelineStage",
    "AsyncPipelineStage",
]
