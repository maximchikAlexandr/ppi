"""Python Railway Oriented Programming vocabulary for PPI.

This package re-exports and aliases the project's ROP primitives from
the existing ``Expression`` library. Do not add a second ``Result``/``Option``
vocabulary (``returns``, handwritten monads, etc.).

All stage-composition, error-handling, and adapter helpers live here.
Concrete pipeline stages are in ``ppi.core.pipelines``,
``ppi.history.pipelines``, and their siblings.
"""

from ppi.rop.types import PipelineStage, StageResult

__all__ = [
    "PipelineStage",
    "StageResult",
]
