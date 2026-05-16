"Upgrade action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, UNIT as UNIT_TYPE, TECHNOLOGY

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Upgrade(UnitAction):
    def __init__(self, action_type: ACTION, unit_id: int) -> None:
        super().__init__(action_type)
        self.unit_id = unit_id

    def is_feasible(self, gs: GameState) -> bool:
        unit = gs.get_actor(self.unit_id)
        tribe = gs.get_tribe(unit.tribe_id)
        tt = tribe.get_tech_tree()
        stars = tribe.get_stars()
        return (
            (unit.get_type() is UNIT_TYPE.BOAT
             and tt.is_researched(TECHNOLOGY.SAILING)
             and stars >= UNIT_TYPE.SHIP.get_cost())
            or
            (unit.get_type() is UNIT_TYPE.SHIP
             and tt.is_researched(TECHNOLOGY.NAVIGATION)
             and stars >= UNIT_TYPE.BATTLESHIP.get_cost())
        )

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        unit = gs.get_actor(self.unit_id)
        tribe = gs.get_tribe(unit.tribe_id)
        board = gs.get_board()
        city = board.get_actor(unit.get_city_id())
        unit_type = unit.get_type()

        if unit_type is UNIT_TYPE.BOAT:
            next_type = UNIT_TYPE.SHIP
        elif unit_type is UNIT_TYPE.SHIP:
            next_type = UNIT_TYPE.BATTLESHIP
        else:
            return False

        new_unit = UNIT_TYPE.create_unit(
            unit.get_position(), unit.get_kills(), unit.is_veteran(),
            unit.get_city_id(), unit.tribe_id, next_type)
        new_unit.set_current_hp(unit.get_current_hp())
        new_unit.set_max_hp(unit.get_max_hp())
        # copy base land unit
        if next_type is UNIT_TYPE.SHIP:
            new_unit.set_base_land_unit(unit.get_base_land_unit())
        else:
            new_unit.set_base_land_unit(unit.get_base_land_unit())

        tribe.subtract_stars(next_type.get_cost())
        turn_status = unit.get_status()

        board.remove_unit_from_board(unit)
        board.remove_unit_from_city(unit, city, tribe)
        board.add_unit(city, new_unit)
        new_unit.set_status(turn_status)
        return True

    def copy(self) -> Upgrade:
        return Upgrade(self.action_type, self.unit_id)

    def __str__(self) -> str:
        return f"UPGRADE by unit {self.unit_id}"
