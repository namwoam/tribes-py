"Recover action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, TURN_STATUS
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Recover(UnitAction):
    def __init__(self, unit_id: int) -> None:
        super().__init__(ACTION.RECOVER)
        self.unit_id = unit_id

    def is_feasible(self, gs: GameState) -> bool:
        unit = gs.get_actor(self.unit_id)
        if unit is None:
            return False
        hp = unit.get_current_hp()
        return unit.is_fresh() and hp < unit.get_max_hp() and hp > 0

    def execute(self, gs: GameState) -> bool:
        unit = gs.get_actor(self.unit_id)
        if unit is None:
            return False
        current_hp = unit.get_current_hp()
        add_hp = cfg.RECOVER_PLUS_HP

        if not self.is_feasible(gs):
            return False

        city_id = gs.get_board().get_city_id_at(unit.get_position().x, unit.get_position().y)
        if city_id != -1:
            cities_id = gs.get_tribe(unit.tribe_id).get_cities_id()
            if city_id in cities_id:
                add_hp += cfg.RECOVER_IN_BORDERS_PLUS_HP

        unit.set_current_hp(min(current_hp + add_hp, unit.get_max_hp()))
        unit.transition_to_status(TURN_STATUS.FINISHED)
        return True

    def copy(self) -> Recover:
        return Recover(self.unit_id)

    def __str__(self) -> str:
        return f"RECOVER by unit {self.unit_id}"
