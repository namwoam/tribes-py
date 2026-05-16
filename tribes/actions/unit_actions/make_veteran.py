"MakeVeteran action + command."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, UNIT as UNIT_TYPE
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class MakeVeteran(UnitAction):
    def __init__(self, unit_id: int) -> None:
        super().__init__(ACTION.MAKE_VETERAN)
        self.unit_id = unit_id

    def is_feasible(self, gs: GameState) -> bool:
        unit = gs.get_actor(self.unit_id)
        if unit.get_type() is UNIT_TYPE.SUPERUNIT:
            return False
        return unit.get_kills() >= cfg.VETERAN_KILLS and not unit.is_veteran()

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        unit = gs.get_actor(self.unit_id)
        unit.set_veteran(True)
        unit.set_max_hp(unit.get_max_hp() + cfg.VETERAN_PLUS_HP)
        unit.set_current_hp(unit.get_max_hp())
        return True

    def copy(self) -> MakeVeteran:
        return MakeVeteran(self.unit_id)

    def __str__(self) -> str:
        return f"MAKE_VETERAN by unit {self.unit_id}"
