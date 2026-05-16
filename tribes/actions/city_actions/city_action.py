"CityAction base class, ported from CityAction.java."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.action import Action
from tribes.types import ACTION

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.utils.vector2d import Vector2d
    from tribes.game.game_state import GameState


class CityAction(Action):
    """Base for all city-targeted actions."""

    def __init__(self, action_type: ACTION) -> None:
        super().__init__(action_type)
        self.city_id: int = -1
        self.target_pos: Optional[Vector2d] = None

    def get_city_id(self) -> int:
        return self.city_id

    def get_target_pos(self) -> Optional[Vector2d]:
        return self.target_pos

    def set_city_id(self, city_id: int) -> None:
        self.city_id = city_id

    def set_target_pos(self, pos: Vector2d) -> None:
        self.target_pos = pos

    def is_feasible(self, gs: GameState) -> bool:
        return False

    def execute(self, gs: GameState) -> bool:
        return False

    def copy(self) -> CityAction:
        return CityAction(self.action_type)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CityAction):
            return False
        return (
            self.city_id == other.city_id
            and self.action_type == other.action_type
            and self.target_pos == other.target_pos
        )
