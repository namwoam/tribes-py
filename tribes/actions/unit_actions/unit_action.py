"UnitAction base class."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.action import Action
from tribes.types import ACTION
from tribes.utils.vector2d import Vector2d

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.actors.units.unit import Unit
    from tribes.game.board import Board
    from tribes.game.game_state import GameState


class UnitAction(Action):
    def __init__(self, action_type: ACTION) -> None:
        super().__init__(action_type)
        self.unit_id: int = -1

    def set_unit_id(self, unit_id: int) -> None:
        self.unit_id = unit_id

    def get_unit_id(self) -> int:
        return self.unit_id

    def unit_in_range(self, attacker: Unit, defender: Unit, b: Board) -> bool:
        target_pos = defender.get_position()
        obs_grid = b.get_tribe(attacker.tribe_id).get_obs_grid()
        if not obs_grid[target_pos.x][target_pos.y]:
            return False
        attacker_pos = attacker.get_position()
        distance = Vector2d.chebychev_distance(attacker_pos, target_pos)
        return distance <= attacker.RANGE

    def is_feasible(self, gs: GameState) -> bool:
        return False

    def execute(self, gs: GameState) -> bool:
        return False

    def copy(self) -> UnitAction:
        return UnitAction(self.action_type)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnitAction):
            return False
        return self.unit_id == other.unit_id and self.action_type == other.action_type
