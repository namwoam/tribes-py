"Move action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, TERRAIN, BUILDING, TURN_STATUS
from tribes.utils.vector2d import Vector2d
from tribes.utils.pathfinder import Pathfinder

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Move(UnitAction):
    def __init__(self, unit_id: int) -> None:
        super().__init__(ACTION.MOVE)
        self.unit_id = unit_id
        self._destination: Optional[Vector2d] = None

    def set_destination(self, dest: Vector2d) -> None:
        self._destination = dest

    def get_destination(self) -> Optional[Vector2d]:
        return self._destination

    def is_feasible(self, gs: GameState) -> bool:
        unit = gs.get_actor(self.unit_id)
        if unit is None or self._destination is None:
            return False
        from tribes.actions.unit_actions.step_move import StepMove
        tp = Pathfinder(unit.get_position(), StepMove(gs, unit))
        if unit.can_move() and gs.get_board().get_unit_at(
                self._destination.x, self._destination.y) is None:
            path = tp.find_path_to(self._destination)
            return path is not None
        return False

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        unit = gs.get_actor(self.unit_id)
        dest = self._destination
        board = gs.get_board()
        tribe = gs.get_tribe(unit.tribe_id)
        dest_terrain = board.get_terrain_at(dest.x, dest.y)

        board.move_unit(unit, unit.get_position().x, unit.get_position().y,
                        dest.x, dest.y, gs.get_random_generator())

        if unit.get_type().is_water_unit():
            if dest_terrain not in (TERRAIN.SHALLOW_WATER, TERRAIN.DEEP_WATER):
                board.disembark(unit, tribe, dest.x, dest.y)
        else:
            if board.get_building_at(dest.x, dest.y) is BUILDING.PORT:
                board.embark(unit, tribe, dest.x, dest.y)

        unit.transition_to_status(TURN_STATUS.MOVED)
        return True

    def copy(self) -> Move:
        m = Move(self.unit_id)
        m._destination = self._destination
        return m

    def __str__(self) -> str:
        return f"MOVE by unit {self.unit_id} to {self._destination}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Move):
            return False
        return super().__eq__(other) and self._destination == other._destination
