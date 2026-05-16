"Examine action + command."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, RESOURCE, EXAMINE_BONUS, UNIT as UNIT_TYPE, TURN_STATUS

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Examine(UnitAction):
    def __init__(self, unit_id: int) -> None:
        super().__init__(ACTION.EXAMINE)
        self.unit_id = unit_id
        self._bonus: Optional[EXAMINE_BONUS] = None

    def get_bonus(self) -> Optional[EXAMINE_BONUS]:
        return self._bonus

    def is_feasible(self, gs: GameState) -> bool:
        unit = gs.get_actor(self.unit_id)
        unit_pos = unit.get_position()
        t = gs.get_tribe(unit.tribe_id)
        if len(t.get_cities_id()) == 0:
            return False
        return (
            unit.is_fresh()
            and gs.get_board().get_resource_at(unit_pos.x, unit_pos.y) is RESOURCE.RUINS
        )

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        unit = gs.get_actor(self.unit_id)
        t = gs.get_tribe(unit.tribe_id)
        rnd = gs.get_random_generator()
        tech_tree = t.get_tech_tree()

        handler_city_id = t.get_cities_id()[0]
        if t.controls_capital():
            handler_city_id = t.get_capital_id()

        all_tech = tech_tree.is_everything_researched()
        bonus = EXAMINE_BONUS.random(rnd)
        while all_tech and bonus is EXAMINE_BONUS.RESEARCH:
            bonus = EXAMINE_BONUS.random(rnd)

        self._bonus = bonus
        board = gs.get_board()
        spawn_pos = unit.get_position().copy()

        if bonus is EXAMINE_BONUS.SUPERUNIT:
            terr = board.get_terrain_at(spawn_pos.x, spawn_pos.y)
            if terr is not None and terr.is_water():
                unit_type = UNIT_TYPE.BATTLESHIP
                new_unit = UNIT_TYPE.create_unit(
                    spawn_pos, 0, False, -1, unit.tribe_id, unit_type
                )
                new_unit.set_base_land_unit(UNIT_TYPE.WARRIOR)
            else:
                new_unit = UNIT_TYPE.create_unit(
                    spawn_pos, 0, False, -1, unit.tribe_id, UNIT_TYPE.SUPERUNIT
                )

            unit_in_city = board.get_unit_at(spawn_pos.x, spawn_pos.y)
            if unit_in_city is not None:
                gs.push_unit(unit_in_city, spawn_pos.x, spawn_pos.y)

            handler_city = gs.get_actor(handler_city_id)
            board.add_unit(handler_city, new_unit)
            # Note: resource NOT cleared for SUPERUNIT (the unit takes the ruins spot)

        elif bonus is EXAMINE_BONUS.RESEARCH:
            researched = tech_tree.research_at_random(rnd)
            if not researched:
                logger.error(
                    f"{gs.get_tick()} ERROR: research_at_random couldn't do "
                    "any research."
                )
            board.set_resource_at(spawn_pos.x, spawn_pos.y, None)

        elif bonus is EXAMINE_BONUS.POP_GROWTH:
            c = gs.get_actor(handler_city_id)
            c.add_population(t, bonus.get_bonus())
            board.set_resource_at(spawn_pos.x, spawn_pos.y, None)

        elif bonus is EXAMINE_BONUS.EXPLORER:
            board.launch_explorer(spawn_pos.x, spawn_pos.y, unit.tribe_id, rnd)
            board.set_resource_at(spawn_pos.x, spawn_pos.y, None)

        elif bonus is EXAMINE_BONUS.RESOURCES:
            t.add_stars(bonus.get_bonus())
            board.set_resource_at(spawn_pos.x, spawn_pos.y, None)

        unit.set_status(TURN_STATUS.FINISHED)
        return True

    def copy(self) -> Examine:
        e = Examine(self.unit_id)
        e._bonus = self._bonus
        return e

    def __str__(self) -> str:
        return f"EXAMINE by unit {self.unit_id} of ruins."

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Examine):
            return False
        return super().__eq__(other) and self._bonus == other._bonus
