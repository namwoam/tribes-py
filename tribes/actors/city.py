"City actor, ported from City.java."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actors.actor import Actor
from tribes.actors.building import Building, Temple
from tribes.types import BUILDING as BUILDING_TYPE
from tribes.utils.vector2d import Vector2d
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.actors.tribe import Tribe


class City(Actor):
    """A city on the game board."""

    def __init__(self, x: int, y: int, tribe_id: int) -> None:
        super().__init__()
        self.position = Vector2d(x, y)
        self.tribe_id = tribe_id
        self._level: int = 1
        self._population: int = 0
        self._population_need: int = 2
        self._is_capital: bool = False
        self._production: int = 0
        self._has_walls: bool = False
        self._bound: int = 1
        self._points_worth: int = 0
        self._units_id: list[int] = []
        self._buildings: list[Building] = []

    # ------------------------------------------------------------------
    # Population / production
    # ------------------------------------------------------------------

    def add_population(self, tribe: Tribe, value: int) -> None:
        if self._population + value < -self._level:
            value = -self._level - self._population
        self._population += value
        tribe.add_score(value * cfg.POINTS_PER_POPULATION)
        self.add_points_worth(value * cfg.POINTS_PER_POPULATION)

    def add_production(self, prod: int) -> None:
        self._production += prod
        if self._production < 0:
            self._production = 0

    def get_production(self) -> int:
        if self._population >= 0:
            capital_bonus = cfg.PROD_CAPITAL_BONUS if self._is_capital else 0
            return self._level + self._production + capital_bonus
        return self._population

    # ------------------------------------------------------------------
    # Buildings
    # ------------------------------------------------------------------

    def add_building(self, game_state, building: Building) -> None:
        self._update_building_effects(game_state, building, negative=False, only_matching=False)
        self._buildings.append(building)

    def remove_building(self, game_state, building: Building) -> None:
        self._update_building_effects(game_state, building, negative=True, only_matching=False)
        self._buildings.remove(building)

    def _update_building_effects(self, game_state, building: Building,
                                  negative: bool, only_matching: bool) -> None:
        multiplier = -1 if negative else 1
        tribe: Tribe = game_state.get_tribe(self.tribe_id)

        btype = building.type

        if btype in (
            BUILDING_TYPE.FARM, BUILDING_TYPE.LUMBER_HUT, BUILDING_TYPE.MINE,
            BUILDING_TYPE.WINDMILL, BUILDING_TYPE.SAWMILL, BUILDING_TYPE.FORGE,
        ):
            self._apply_bonus(game_state, building, is_population=True,
                              only_matching=only_matching, multiplier=multiplier)

        elif btype is BUILDING_TYPE.PORT:
            if not only_matching:
                self.add_population(tribe, btype.get_bonus() * multiplier)
            self._apply_bonus(game_state, building, is_population=False,
                              only_matching=only_matching, multiplier=multiplier)

        elif btype is BUILDING_TYPE.CUSTOMS_HOUSE:
            self._apply_bonus(game_state, building, is_population=False,
                              only_matching=only_matching, multiplier=multiplier)

        elif btype in (
            BUILDING_TYPE.TEMPLE, BUILDING_TYPE.WATER_TEMPLE,
            BUILDING_TYPE.MOUNTAIN_TEMPLE, BUILDING_TYPE.FOREST_TEMPLE,
        ):
            if not only_matching:
                self.add_population(tribe, btype.get_bonus() * multiplier)
            score_diff = (
                building.get_points() if (negative and isinstance(building, Temple))
                else cfg.TEMPLE_POINTS[0]
            )
            tribe.add_score(score_diff)

        elif btype in (
            BUILDING_TYPE.ALTAR_OF_PEACE, BUILDING_TYPE.EMPERORS_TOMB,
            BUILDING_TYPE.EYE_OF_GOD, BUILDING_TYPE.GATE_OF_POWER,
            BUILDING_TYPE.PARK_OF_FORTUNE, BUILDING_TYPE.TOWER_OF_WISDOM,
            BUILDING_TYPE.GRAND_BAZAR,
        ):
            if not only_matching:
                self.add_population(tribe, btype.get_bonus() * multiplier)
            tribe.add_score(cfg.MONUMENT_POINTS * multiplier)

    # Kept accessible as package method (called by Tribe)
    update_building_effects = _update_building_effects

    def _apply_bonus(self, game_state, building: Building, is_population: bool,
                     only_matching: bool, multiplier: int) -> None:
        is_base = building.type.is_base()
        city_to_add_to: City = self
        board = game_state.get_board()
        tribe: Tribe = game_state.get_tribe(self.tribe_id)

        if is_base and is_population and not only_matching:
            self.add_population(tribe, multiplier * building.get_bonus())

        for adj_pos in building.position.neighborhood(1, 0, board.get_size()):
            b = board.get_building_at(adj_pos.x, adj_pos.y)
            if b is not None and building.type.get_matching_building() is b:
                city_id = board.get_city_id_at(adj_pos.x, adj_pos.y)
                if city_id == self.actor_id:
                    existing_building = self.get_building(adj_pos.x, adj_pos.y)
                    city_to_add_to = self
                elif tribe.controls_city(city_id):
                    city_obj = game_state.get_actor(city_id)
                    existing_building = city_obj.get_building(adj_pos.x, adj_pos.y)
                    city_to_add_to = city_obj
                else:
                    return

                if existing_building is not None:
                    bonus_to_add = (
                        existing_building.get_bonus() if is_base
                        else building.get_bonus()
                    )
                    if is_population:
                        city_to_add_to.add_population(tribe, bonus_to_add * multiplier)
                    else:
                        city_to_add_to.add_production(bonus_to_add * multiplier)

    def get_building(self, x: int, y: int) -> Optional[Building]:
        for b in self._buildings:
            if b.position.x == x and b.position.y == y:
                return b
        return None

    # ------------------------------------------------------------------
    # Level up
    # ------------------------------------------------------------------

    def can_level_up(self) -> bool:
        return self._population >= self._population_need

    def level_up(self) -> None:
        self._level += 1
        self._population -= self._population_need
        self._population_need = self._level + 1

    # ------------------------------------------------------------------
    # Units
    # ------------------------------------------------------------------

    def add_unit(self, unit_id: int) -> None:
        if self.can_add_unit():
            self._units_id.append(unit_id)

    def can_add_unit(self) -> bool:
        return len(self._units_id) < (self._level + 1)

    def remove_unit(self, unit_id: int) -> None:
        for i, uid in enumerate(self._units_id):
            if uid == unit_id:
                self._units_id.pop(i)
                return
        logger.error(f"Unit ID {unit_id} does not belong to city {self.actor_id}")

    def remove_unit_by_index(self, index: int) -> int:
        return self._units_id.pop(index)

    def clear_units(self) -> None:
        self._units_id.clear()

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    def _copy_buildings(self) -> list[Building]:
        return [b.copy() for b in self._buildings]

    def copy(self, hide_info: bool = False) -> City:
        c = City(self.position.x, self.position.y, self.tribe_id)
        c._level = self._level
        c._population = 0 if hide_info else self._population
        c._population_need = self._population_need
        c._is_capital = self._is_capital
        c._production = 0 if hide_info else self._production
        c._has_walls = self._has_walls
        c._bound = self._bound
        c.actor_id = self.actor_id
        c._points_worth = self._points_worth
        c._buildings = self._copy_buildings()
        c._units_id = [] if hide_info else list(self._units_id)
        return c

    # ------------------------------------------------------------------
    # Getters / setters
    # ------------------------------------------------------------------

    def get_level(self) -> int:
        return self._level

    def get_population(self) -> int:
        return self._population

    def is_capital(self) -> bool:
        return self._is_capital

    def set_capital(self, is_capital: bool) -> None:
        self._is_capital = is_capital

    def get_population_need(self) -> int:
        return self._population_need

    def set_walls(self, walls: bool) -> None:
        self._has_walls = walls

    def has_walls(self) -> bool:
        return self._has_walls

    def get_bound(self) -> int:
        return self._bound

    def set_bound(self, b: int) -> None:
        self._bound = b

    def get_units_id(self) -> list[int]:
        return self._units_id

    def get_num_units(self) -> int:
        return len(self._units_id)

    def set_tribe_id(self, tribe_id: int) -> None:
        self.tribe_id = tribe_id

    def get_buildings(self) -> list[Building]:
        return self._buildings

    def set_buildings(self, buildings: list[Building]) -> None:
        self._buildings = buildings

    def add_points_worth(self, points: int) -> None:
        self._points_worth += points

    def get_points_worth(self) -> int:
        return self._points_worth

    def set_population(self, pop_value: int) -> None:
        self._population = pop_value

    def set_production(self, prod_value: int) -> None:
        self._production = prod_value
