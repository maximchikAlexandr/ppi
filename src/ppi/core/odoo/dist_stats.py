"""Pure statistics helpers (distribution summary) extracted from the pipeline.

``build_distribution_stats`` is a pure function over an iterable of numbers;
it does not touch the filesystem or radon/complexipy. Value objects for the
distribution live in :mod:`ppi.core.odoo.complexity`.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Iterable

import deal

from ppi.core.value_objects import ContractError

__all__ = ["DistributionStats", "build_distribution_stats"]


# ponytail: DistributionStats is a plain class (not a dataclass); the count
# invariant stays in __init__ (no factory, deal.inv does not fire on init).


class DistributionStats:
    """Immutable distribution summary for one metric family.

    Frozen via ``__slots__`` + tuple-ish equality; kept as a small class so it
    can be reused by both the legacy pipeline and the new typed modules
    without a dataclass import dance. ``count`` is non-negative, all moments
    default to 0.0 when empty.
    """

    __slots__ = ("count", "mean", "median", "p95", "max")

    def __init__(
        self,
        count: int = 0,
        mean: float = 0.0,
        median: float = 0.0,
        p95: float = 0.0,
        max: float = 0.0,
    ) -> None:
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ContractError(f"DistributionStats.count must be non-negative int, got {count!r}")
        self.count = count
        self.mean = float(mean)
        self.median = float(median)
        self.p95 = float(p95)
        self.max = float(max)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DistributionStats):
            return NotImplemented
        return (
            self.count == other.count
            and self.mean == other.mean
            and self.median == other.median
            and self.p95 == other.p95
            and self.max == other.max
        )

    def __hash__(self) -> int:
        return hash((self.count, self.mean, self.median, self.p95, self.max))

    def __repr__(self) -> str:
        return (
            f"DistributionStats(count={self.count}, mean={self.mean}, "
            f"median={self.median}, p95={self.p95}, max={self.max})"
        )

    @classmethod
    def empty(cls) -> DistributionStats:
        """Build an empty distribution (count 0, moments 0)."""
        return cls()

    @classmethod
    @deal.pre(
        lambda cls, count=0, mean=0.0, median=0.0, p95=0.0, max=0.0: (
            isinstance(count, int) and not isinstance(count, bool) and count >= 0
        ),
        exception=ContractError,
    )
    def of(
        cls,
        count: int = 0,
        mean: float = 0.0,
        median: float = 0.0,
        p95: float = 0.0,
        max: float = 0.0,
    ) -> DistributionStats:
        """Build a distribution stats value object (precondition via deal)."""
        return cls(count=count, mean=mean, median=median, p95=p95, max=max)


def build_distribution_stats(values: Iterable[int | float]) -> DistributionStats:
    """Build count/mean/median/p95/max summary from raw values (pure)."""
    values_list = list(values)
    if not values_list:
        return DistributionStats.empty()

    sorted_values = sorted(values_list)
    index = max(0, math.ceil(0.95 * len(sorted_values)) - 1)
    return DistributionStats(
        count=len(values_list),
        mean=float(statistics.mean(values_list)),
        median=float(statistics.median(values_list)),
        p95=float(sorted_values[index]),
        max=float(max(values_list)),
    )
