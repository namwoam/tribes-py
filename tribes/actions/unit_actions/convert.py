"Convert action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, UNIT as UNIT_TYPE, TURN_STATUS
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Convert(UnitAction):
    def __init__(self, unit_id: int) -> None:
        super().__init__(ACTION.CONVERT)
        self.unit_id = unit_id
        self._target_id: int = -1

    def set_target_id(self, target_id: int) -> None:
        self._target_id = target_id

    def get_target_id(self) -> int:
        return self._target_id

    def is_feasible(self, gs: GameState) -> bool:
        unit = gs.get_actor(self.unit_id)
        target = gs.get_actor(self._target_id)
        if unit.get_type() is not UNIT_TYPE.MIND_BENDER:
            return False
        if target is None or not unit.can_attack():
            return False
        return self.unit_in_range(unit, target, gs.get_board())

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        d = gs.get_board().get_diplomacy()
        unit = gs.get_actor(self.unit_id)
        target = gs.get_actor(self._target_id)
        target_tribe = gs.get_tribe(target.tribe_id)

        city_id = target.get_city_id()
        c = gs.get_actor(city_id)
        gs.get_board().remove_unit_from_city(target, c, target_tribe)

        target.tribe_id = unit.tribe_id
        gs.get_active_tribe().add_extra_unit(target)

        d.update_allegiance(cfg.CONVERT_REPERCUSSION, unit.tribe_id, target.tribe_id)
        d.check_consequences(cfg.CONVERT_REPERCUSSION, unit.tribe_id, target.tribe_id)

        unit.transition_to_status(TURN_STATUS.ATTACKED)
        target.set_status(TURN_STATUS.FINISHED)
        return True

    def copy(self) -> Convert:
        c = Convert(self.unit_id)
        c._target_id = self._target_id
        return c

    def __str__(self) -> str:
        return f"CONVERT by unit {self.unit_id} to unit {self._target_id}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Convert):
            return False
        return super().__eq__(other) and self._target_id == other._target_id
