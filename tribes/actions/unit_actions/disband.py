"Disband action + command."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, TECHNOLOGY

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Disband(UnitAction):
    def __init__(self, unit_id: int) -> None:
        super().__init__(ACTION.DISBAND)
        self.unit_id = unit_id

    def is_feasible(self, gs: GameState) -> bool:
        unit = gs.get_actor(self.unit_id)
        tt = gs.get_tribe(unit.tribe_id).get_tech_tree()
        return unit.is_fresh() and tt.is_researched(TECHNOLOGY.FREE_SPIRIT)

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        unit = gs.get_actor(self.unit_id)
        b = gs.get_board()
        t = gs.get_tribe(unit.tribe_id)
        c = b.get_actor(unit.get_city_id())
        stars_gained = int(unit.COST / 2.0)
        t.add_stars(stars_gained)
        b.remove_unit_from_board(unit)
        b.remove_unit_from_city(unit, c, t)
        t.subtract_score(unit.get_type().get_points())
        return True

    def copy(self) -> Disband:
        return Disband(self.unit_id)

    def __str__(self) -> str:
        return f"DISBAND of unit {self.unit_id}"
