"Building and Temple actors, ported from Building.java and Temple.java."
from __future__ import annotations

from typing import TYPE_CHECKING

from tribes.types import BUILDING as BUILDING_TYPE
from tribes.utils.vector2d import Vector2d
from tribes import config as cfg

if TYPE_CHECKING:
    pass


class Building:
    """A building placed on the board belonging to a city."""

    def __init__(self, x: int, y: int, btype: BUILDING_TYPE, city_id: int) -> None:
        self.position: Vector2d = Vector2d(x, y)
        self.type: BUILDING_TYPE = btype
        self.city_id: int = city_id

    def copy(self) -> Building:
        return Building(self.position.x, self.position.y, self.type, self.city_id)

    def get_bonus(self) -> int:
        return self.type.get_bonus()


class Temple(Building):
    """A temple building that levels up and generates score over turns."""

    def __init__(self, x: int, y: int, btype: BUILDING_TYPE, city_id: int) -> None:
        super().__init__(x, y, btype, city_id)
        self._level: int = 0
        self._turns_to_score: int = 0
        self._level_up()

    def _level_up(self) -> None:
        self._level += 1
        self._turns_to_score = cfg.TEMPLE_TURNS_TO_SCORE

    def new_turn(self) -> int:
        """Advance one turn and return score produced (0 if none)."""
        if self._level < 5:
            self._turns_to_score -= 1
            if self._turns_to_score == 0:
                self._level_up()
                return cfg.TEMPLE_POINTS[self._level - 1]
        return 0

    def get_points(self) -> int:
        """Total points this temple is worth so far."""
        return sum(cfg.TEMPLE_POINTS[i] for i in range(self._level))

    def copy(self) -> Temple:
        t = Temple.__new__(Temple)
        Building.__init__(t, self.position.x, self.position.y, self.type, self.city_id)
        t._level = self._level
        t._turns_to_score = self._turns_to_score
        return t

    def get_level(self) -> int:
        return self._level

    def get_turns_to_score(self) -> int:
        return self._turns_to_score
