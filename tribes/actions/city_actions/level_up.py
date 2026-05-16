"LevelUp action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.city_actions.city_action import CityAction
from tribes.types import ACTION, CITY_LEVEL_UP, UNIT as UNIT_TYPE
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class LevelUp(CityAction):
    def __init__(self, city_id: int) -> None:
        super().__init__(ACTION.LEVEL_UP)
        self.city_id = city_id
        self._bonus: Optional[CITY_LEVEL_UP] = None

    def get_bonus(self) -> Optional[CITY_LEVEL_UP]:
        return self._bonus

    def set_bonus(self, bonus: CITY_LEVEL_UP) -> None:
        self._bonus = bonus

    def is_feasible(self, gs: GameState) -> bool:
        city = gs.get_actor(self.city_id)
        if self._bonus is None:
            return False
        return city.can_level_up() and self._bonus.valid_type(city.get_level())

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        city = gs.get_actor(self.city_id)
        tribe = gs.get_board().get_tribe(city.tribe_id)
        city_pos = city.get_position()
        bonus = self._bonus

        if bonus.grants_monument():
            tribe.city_maxed_up()

        tribe.add_score(bonus.get_level_up_points())
        city.add_points_worth(bonus.get_level_up_points())
        city.level_up()

        if bonus is CITY_LEVEL_UP.WORKSHOP:
            city.add_production(cfg.CITY_LEVEL_UP_WORKSHOP_PROD)
        elif bonus is CITY_LEVEL_UP.EXPLORER:
            gs.get_board().launch_explorer(city_pos.x, city_pos.y,
                                           city.tribe_id, gs.get_random_generator())
        elif bonus is CITY_LEVEL_UP.CITY_WALL:
            city.set_walls(True)
        elif bonus is CITY_LEVEL_UP.RESOURCES:
            tribe.add_stars(cfg.CITY_LEVEL_UP_RESOURCES)
        elif bonus is CITY_LEVEL_UP.POP_GROWTH:
            city.add_population(tribe, cfg.CITY_LEVEL_UP_POP_GROWTH)
        elif bonus is CITY_LEVEL_UP.BORDER_GROWTH:
            gs.get_board().expand_border(city)
        elif bonus is CITY_LEVEL_UP.PARK:
            tribe.add_score(cfg.CITY_LEVEL_UP_PARK)
            city.add_points_worth(cfg.CITY_LEVEL_UP_PARK)
        elif bonus is CITY_LEVEL_UP.SUPERUNIT:
            unit_in_city = gs.get_board().get_unit_at(city_pos.x, city_pos.y)
            if unit_in_city is not None:
                gs.push_unit(unit_in_city, city_pos.x, city_pos.y)
            super_unit = UNIT_TYPE.create_unit(
                city_pos, 0, False, city.actor_id, city.tribe_id, UNIT_TYPE.SUPERUNIT)
            gs.get_board().add_unit(city, super_unit)

        return True

    def copy(self) -> LevelUp:
        lu = LevelUp(self.city_id)
        lu._bonus = self._bonus
        if self.target_pos is not None:
            lu.target_pos = self.target_pos.copy()
        return lu

    def __str__(self) -> str:
        return f"LEVEL_UP by city {self.city_id} with bonus {self._bonus}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LevelUp):
            return False
        return super().__eq__(other) and self._bonus == other._bonus
