"PathNode for A*/Dijkstra pathfinding, ported from PathNode.java."

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tribes.utils.vector2d import Vector2d

MAX_CAPACITY = 10000


class PathNode:
    """A node used by the Pathfinder."""

    __slots__ = (
        "_position",
        "_parent",
        "_total_cost",
        "_estimated_cost",
        "_visited",
        "_id",
    )

    def __init__(self, position: Vector2d, total_cost: float = 0.0) -> None:
        from tribes.utils.vector2d import Vector2d as _V

        self._position: Vector2d = _V(position.x, position.y)
        self._parent: Optional[PathNode] = None
        self._total_cost: float = total_cost
        self._estimated_cost: float = 0.0
        self._visited: bool = False
        self._id: int = position.x * MAX_CAPACITY + position.y

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_id(self) -> int:
        return self._id

    def get_x(self) -> int:
        return self._position.x

    def get_y(self) -> int:
        return self._position.y

    def get_position(self) -> Vector2d:
        return self._position

    def get_parent(self) -> Optional[PathNode]:
        return self._parent

    def set_parent(self, parent: Optional[PathNode]) -> None:
        self._parent = parent

    def get_total_cost(self) -> float:
        return self._total_cost

    def set_total_cost(self, cost: float) -> None:
        self._total_cost = cost

    def get_estimated_cost(self) -> float:
        return self._estimated_cost

    def set_estimated_cost(self, cost: float) -> None:
        self._estimated_cost = cost

    def is_visited(self) -> bool:
        return self._visited

    def set_visited(self, visited: bool) -> None:
        self._visited = visited

    # ------------------------------------------------------------------
    # Comparison (priority queue)
    # ------------------------------------------------------------------

    def __lt__(self, other: PathNode) -> bool:
        return (self._total_cost + self._estimated_cost) < (
            other._total_cost + other._estimated_cost
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PathNode):
            return self._position == other._position
        return False

    def __hash__(self) -> int:
        return self._id
