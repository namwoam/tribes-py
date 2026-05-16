"2-D integer vector ported from Vector2d.java."
from __future__ import annotations

import math
from typing import Optional


class Vector2d:
    """Integer 2-D position / vector used throughout the game."""

    __slots__ = ("x", "y")

    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y

    # ------------------------------------------------------------------
    # Core Python protocol
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vector2d):
            return self.x == other.x and self.y == other.y
        return False

    def __hash__(self) -> int:
        return self.x * 20 + self.y

    def __repr__(self) -> str:
        return f"{self.x} : {self.y}"

    # ------------------------------------------------------------------
    # Copy / mutation
    # ------------------------------------------------------------------

    def copy(self) -> Vector2d:
        return Vector2d(self.x, self.y)

    def set(self, x_or_v, y: Optional[int] = None) -> None:
        if isinstance(x_or_v, Vector2d):
            self.x = x_or_v.x
            self.y = x_or_v.y
        else:
            self.x = x_or_v
            self.y = y  # type: ignore[assignment]

    def zero(self) -> None:
        self.x = 0
        self.y = 0

    # ------------------------------------------------------------------
    # Arithmetic — follows Java semantics:
    #   add(Vector2d) returns NEW vector; add(int,int) mutates self.
    # ------------------------------------------------------------------

    def add(self, x_or_v, y: Optional[int] = None, w: Optional[int] = None) -> Vector2d:
        if isinstance(x_or_v, Vector2d):
            v = x_or_v
            if w is not None:
                # weighted addition: mutates self
                self.x += w * v.x
                self.y += w * v.y
                return self
            # returns new vector
            return Vector2d(self.x + v.x, self.y + v.y)
        else:
            # add(int, int): mutates self and returns self
            self.x += x_or_v
            self.y += y  # type: ignore[operator]
            return self

    def subtract(self, x_or_v, y: Optional[int] = None) -> Vector2d:
        if isinstance(x_or_v, Vector2d):
            v = x_or_v
            return Vector2d(self.x - v.x, self.y - v.y)
        else:
            self.x -= x_or_v
            self.y -= y  # type: ignore[operator]
            return self

    def mul(self, fac: int) -> Vector2d:
        self.x *= fac
        self.y *= fac
        return self

    def wrap(self, w: int, h: int) -> Vector2d:
        self.x = (self.x + w) % w
        self.y = (self.y + h) % h
        return self

    def rotate(self, theta: float) -> None:
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        nx = int(self.x * cos_t - self.y * sin_t)
        ny = int(self.x * sin_t + self.y * cos_t)
        self.x = nx
        self.y = ny

    # ------------------------------------------------------------------
    # Distance / magnitude
    # ------------------------------------------------------------------

    @staticmethod
    def sqr(x: int) -> int:
        return x * x

    def sq_dist(self, v: Vector2d) -> int:
        return Vector2d.sqr(self.x - v.x) + Vector2d.sqr(self.y - v.y)

    def mag(self) -> float:
        return math.sqrt(Vector2d.sqr(self.x) + Vector2d.sqr(self.y))

    def dist(self, v_or_x, y: Optional[int] = None) -> float:
        if isinstance(v_or_x, Vector2d):
            return math.sqrt(self.sq_dist(v_or_x))
        return math.sqrt(Vector2d.sqr(self.x - v_or_x) + Vector2d.sqr(self.y - y))  # type: ignore[arg-type]

    def custom_dist(self, v_or_x, y: Optional[int] = None) -> float:
        if isinstance(v_or_x, Vector2d):
            return max(abs(self.x - v_or_x.x), abs(self.y - v_or_x.y))
        return max(abs(self.x - v_or_x), abs(self.y - y))  # type: ignore[arg-type]

    def theta(self) -> float:
        return math.atan2(self.y, self.x)

    def normalise(self) -> None:
        m = self.mag()
        if m == 0:
            self.x = self.y = 0
        else:
            self.x = int(self.x / m)
            self.y = int(self.y / m)

    def scalar_product(self, v: Vector2d) -> int:
        return self.x * v.x + self.y * v.y

    def dot(self, v: Vector2d) -> int:
        return self.x * v.x + self.y * v.y

    def unit_vector(self) -> Vector2d:
        mag = self.mag()
        if mag > 0:
            return Vector2d(int(self.x / mag), int(self.y / mag))
        return Vector2d(1, 0)

    def adjacent_to(self, v: Vector2d) -> bool:
        return abs(v.x - self.x) <= 1 and abs(v.y - self.y) <= 1

    # ------------------------------------------------------------------
    # Neighborhood
    # ------------------------------------------------------------------

    def neighborhood(self, radius: int, min_val: int, max_val: int) -> list[Vector2d]:
        """Return neighbors within Chebyshev radius, excluding self, within bounds."""
        result: list[Vector2d] = []
        for i in range(self.x - radius, self.x + radius + 1):
            for j in range(self.y - radius, self.y + radius + 1):
                if (i != self.x or j != self.y) and (
                    min_val <= i < max_val and min_val <= j < max_val
                ):
                    result.append(Vector2d(i, j))
        return result

    # ------------------------------------------------------------------
    # Static distance helpers
    # ------------------------------------------------------------------

    @staticmethod
    def manhattan_distance(p1: Vector2d, p2: Vector2d) -> float:
        return abs(p1.x - p2.x) + abs(p1.y - p2.y)

    @staticmethod
    def chebychev_distance(p1: Vector2d, p2: Vector2d) -> float:
        return max(abs(p1.x - p2.x), abs(p1.y - p2.y))

    @staticmethod
    def euclidean_distance(p1: Vector2d, p2: Vector2d) -> float:
        return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
