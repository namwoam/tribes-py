"Abstract base class for all game actors, ported from Actor.java."
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tribes.utils.vector2d import Vector2d


class Actor(ABC):
    """Abstract base for all actors (cities, units, tribes)."""

    def __init__(self) -> None:
        self.actor_id: int = -1
        self.tribe_id: int = -1
        self.position: Optional[Vector2d] = None

    @abstractmethod
    def copy(self, hide_info: bool) -> Actor:
        """Return a (possibly hidden) copy of this actor."""

    def set_actor_id(self, actor_id: int) -> None:
        self.actor_id = actor_id

    def get_actor_id(self) -> int:
        return self.actor_id

    def set_tribe_id(self, tribe_id: int) -> None:
        self.tribe_id = tribe_id

    def get_tribe_id(self) -> int:
        return self.tribe_id

    def set_position(self, x: int, y: int) -> None:
        from tribes.utils.vector2d import Vector2d
        self.position = Vector2d(x, y)

    def get_position(self) -> Optional[Vector2d]:
        return self.position
