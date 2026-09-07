"""Abstract quantale operations over non-negative coordinate vectors."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class QuantaleValue:
    """Immutable vector in [0, inf]^d."""

    coords: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.coords) == 0:
            raise ValueError("QuantaleValue must have at least one coordinate")
        for c in self.coords:
            if math.isnan(c) or c < 0:
                raise ValueError(
                    f"QuantaleValue coordinates must be non-negative, got {c}"
                )

    @property
    def dim(self) -> int:
        return len(self.coords)

    def _check_same_dim(self, other: "QuantaleValue") -> None:
        if self.dim != other.dim:
            raise ValueError(f"Dimension mismatch: {self.dim} vs {other.dim}")

    def tensor(self, other: "QuantaleValue") -> "QuantaleValue":
        """Componentwise addition."""
        self._check_same_dim(other)
        return QuantaleValue(
            tuple(a + b for a, b in zip(self.coords, other.coords))
        )

    def join(self, other: "QuantaleValue") -> "QuantaleValue":
        """Componentwise maximum."""
        self._check_same_dim(other)
        return QuantaleValue(
            tuple(max(a, b) for a, b in zip(self.coords, other.coords))
        )

    def __le__(self, other: "QuantaleValue") -> bool:
        """Componentwise partial order."""
        self._check_same_dim(other)
        return all(a <= b for a, b in zip(self.coords, other.coords))

    def dominates(self, other: "QuantaleValue") -> bool:
        """Strict componentwise dominance."""
        self._check_same_dim(other)
        return self <= other and self.coords != other.coords

    def comparable_to(self, other: "QuantaleValue") -> bool:
        """Whether either value is componentwise below the other."""
        return self <= other or other <= self

    def is_finite(self) -> bool:
        return all(math.isfinite(c) for c in self.coords)

    def __repr__(self) -> str:
        return f"QuantaleValue{self.coords}"


def unit(dim: int) -> QuantaleValue:
    """Return the all-zero vector."""
    return QuantaleValue(tuple(0.0 for _ in range(dim)))


def top(dim: int) -> QuantaleValue:
    """Return the all-infinity vector."""
    return QuantaleValue(tuple(float("inf") for _ in range(dim)))


def big_join(values: list[QuantaleValue]) -> QuantaleValue:
    """Join all values using componentwise maximum."""
    if not values:
        raise ValueError(
            "big_join of an empty list is undefined — caller must handle this case"
        )

    result = values[0]
    for value in values[1:]:
        result = result.join(value)

    return result