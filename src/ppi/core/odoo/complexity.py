"""Complexity value objects isolating complexity math from AST/file parsing.

Score and count value objects guard their invariants (non-negative, positive
source line) so complexity calculations become testable without the filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ppi.core.odoo.dist_stats import DistributionStats, build_distribution_stats
from ppi.core.value_objects import ContractError

__all__ = [
    "ComplexityMetrics",
    "FileComplexityInfo",
    "FileComplexityAnalysisResult",
]


@dataclass(frozen=True, slots=True)
class ComplexityMetrics:
    """Aggregated complexity metrics for one file or module."""

    cyclomatic: DistributionStats = field(default_factory=DistributionStats.empty)
    cognitive: DistributionStats = field(default_factory=DistributionStats.empty)
    jones: DistributionStats = field(default_factory=DistributionStats.empty)

    @classmethod
    def empty(cls) -> ComplexityMetrics:
        return cls()

    @classmethod
    def from_score_tuples(
        cls,
        cyclomatic: tuple[int, ...],
        cognitive: tuple[int, ...],
        jones: tuple[int, ...],
    ) -> ComplexityMetrics:
        return cls(
            cyclomatic=build_distribution_stats(cyclomatic),
            cognitive=build_distribution_stats(cognitive),
            jones=build_distribution_stats(jones),
        )


@dataclass(frozen=True, slots=True)
class FileComplexityInfo:
    """Complexity metrics for one production Python file."""

    relative_path: str
    lines: int
    function_count: int
    jones_line_count: int
    complexity: ComplexityMetrics
    parse_error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.lines, int) or self.lines < 0:
            raise ContractError(f"FileComplexityInfo.lines must be >= 0, got {self.lines!r}")
        if not isinstance(self.function_count, int) or self.function_count < 0:
            raise ContractError(
                f"FileComplexityInfo.function_count must be >= 0, got {self.function_count!r}"
            )
        if not isinstance(self.jones_line_count, int) or self.jones_line_count < 0:
            raise ContractError(
                f"FileComplexityInfo.jones_line_count must be >= 0, got {self.jones_line_count!r}"
            )


@dataclass(frozen=True, slots=True)
class FileComplexityAnalysisResult:
    """Pure analysis result for one Python file complexity pass."""

    file_complexity_info: FileComplexityInfo
    cyclomatic_values: tuple[int, ...] = ()
    cognitive_values: tuple[int, ...] = ()
    jones_values: tuple[int, ...] = ()
