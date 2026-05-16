"Capture action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, TERRAIN, TURN_STATUS
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Capture(UnitAction):
    def __init__(self, unit_id: int) -> None:
        super().__init__(ACTION.CAPTURE)
        self.unit_id = unit_id
        self._target_city_id: int = -1
        self._capture_type: Optional[TERRAIN] = None

    def set_target_city(self, city_id: int) -> None:
        self._target_city_id = city_id

    def get_target_city(self) -> int:
        return self._target_city_id

    def set_capture_type(self, ct: TERRAIN) -> None:
        self._capture_type = ct

    def get_capture_type(self) -> Optional[TERRAIN]:
        return self._capture_type

    def is_feasible(self, gs: GameState) -> bool:
        unit = gs.get_actor(self.unit_id)
        if not unit.is_fresh():
            return False
        b = gs.get_board()
        if self._capture_type is TERRAIN.CITY:
            target_city = gs.get_actor(self._target_city_id)
            if target_city is None:
                return False
            target_pos = target_city.get_position()
            if b.get_unit_at(target_pos.x, target_pos.y) is None:
                return False
            unit_pos = unit.get_position()
            if not target_pos == unit_pos:
                return False
            return target_city.tribe_id != unit.tribe_id
        elif self._capture_type is TERRAIN.VILLAGE:
            unit_pos = unit.get_position()
            return b.get_terrain_at(unit_pos.x, unit_pos.y) is TERRAIN.VILLAGE
        return False

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        unit = gs.get_actor(self.unit_id)
        b = gs.get_board()
        this_tribe = b.get_tribe(unit.tribe_id)

        if self._capture_type is TERRAIN.CITY:
            target_city = gs.get_actor(self._target_city_id)
            target_tribe = b.get_tribe(target_city.tribe_id)

            target_tribe.subtract_score(target_city.get_points_worth())
            this_tribe.add_score(target_city.get_points_worth())

            d = b.get_diplomacy()
            d.update_allegiance(cfg.CAPTURE_REPERCUSSION, this_tribe.tribe_id, target_tribe.tribe_id)
            d.check_consequences(cfg.CAPTURE_REPERCUSSION, this_tribe.tribe_id, target_tribe.tribe_id)

            unit.set_status(TURN_STATUS.FINISHED)
            city_pos = target_city.get_position()
            return b.capture(gs, this_tribe, city_pos.x, city_pos.y)
        elif self._capture_type is TERRAIN.VILLAGE:
            unit.set_status(TURN_STATUS.FINISHED)
            unit_pos = unit.get_position()
            return b.capture(gs, this_tribe, unit_pos.x, unit_pos.y)
        return False

    def copy(self) -> Capture:
        c = Capture(self.unit_id)
        c._target_city_id = self._target_city_id
        c._capture_type = self._capture_type
        return c

    def __str__(self) -> str:
        return f"CAPTURE by unit {self.unit_id} of target {self._capture_type}: {self._target_city_id}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Capture):
            return False
        return (super().__eq__(other)
                and self._target_city_id == other._target_city_id
                and self._capture_type == other._capture_type)
