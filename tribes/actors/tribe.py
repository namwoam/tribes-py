"Tribe actor, ported from Tribe.java."

from __future__ import annotations

import logging
import random as _random
from typing import TYPE_CHECKING, Optional

from tribes import config as cfg, constants as C
from tribes.actors.actor import Actor
from tribes.tech_tree import TechnologyTree
from tribes.types import (
    BUILDING as BUILDING_TYPE,
    MONUMENT_STATUS,
    RESULT,
    TECHNOLOGY,
    TRIBE as TRIBE_TYPE,
)
from tribes.utils.vector2d import Vector2d

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.actors.city import City
    from tribes.actors.units.unit import Unit


class Tribe(Actor):
    """A player tribe in the game."""

    def __init__(
        self,
        tribe_type: TRIBE_TYPE,
        tribe_id: Optional[int] = None,
        city_id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._tribe: TRIBE_TYPE = tribe_type
        if tribe_id is not None:
            self.tribe_id = tribe_id
        if city_id is not None:
            self._cities_id: list[int] = [city_id]
        else:
            self._cities_id = []
        self._capital_id: int = -1
        self._tech_tree: TechnologyTree = TechnologyTree()
        self._stars: int = cfg.INITIAL_STARS
        self._winner: RESULT = RESULT.INCOMPLETE
        self._score: int = 0
        self._obs_grid: list[list[bool]] = []
        self._connected_cities: list[int] = []
        self._monuments: dict[BUILDING_TYPE, MONUMENT_STATUS] = (
            BUILDING_TYPE.init_monuments()
        )
        self._tribes_met: list[int] = []
        self._extra_units: list[int] = []
        self._n_kills: int = 0
        self._n_pacifist_count: int = 0
        self._stars_sent: int = 0
        self._has_declared_war: bool = False
        self._n_wars_declared: int = 0
        self._n_stars_sent: int = 0

        self._init()

    def _init(self) -> None:
        self._tech_tree = TechnologyTree()
        init_tech = self._tribe.get_initial_tech()
        if init_tech is not None:
            self._tech_tree.do_research_init(init_tech)
            self._score = init_tech.get_points()
        self._cities_id = []
        self._stars = cfg.INITIAL_STARS
        self._tribes_met = []
        self._extra_units = []
        self._connected_cities = []
        self._monuments = BUILDING_TYPE.init_monuments()
        self._n_kills = 0
        self._n_pacifist_count = 0

    def init_obs_grid(self, size: int) -> None:
        if C.PLAY_WITH_FULL_OBS:
            self._obs_grid = [[True] * size for _ in range(size)]
        else:
            self._obs_grid = [[False] * size for _ in range(size)]

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    def copy(self, hide_info: bool = False) -> Tribe:
        tc = Tribe(self._tribe)
        tc.actor_id = self.actor_id
        tc.tribe_id = self.tribe_id
        tc._stars = 0 if hide_info else self._stars
        tc._winner = self._winner
        tc._score = self._score
        tc._capital_id = self._capital_id
        tc._n_kills = 0 if hide_info else self._n_kills
        tc._n_pacifist_count = 0 if hide_info else self._n_pacifist_count
        tc._stars_sent = self._stars_sent
        tc._has_declared_war = self._has_declared_war
        tc._n_wars_declared = self._n_wars_declared
        tc._n_stars_sent = self._n_stars_sent
        tc._tech_tree = TechnologyTree() if hide_info else self._tech_tree.copy()

        size = len(self._obs_grid)
        tc._obs_grid = [[True] * size for _ in range(size)]
        if not hide_info:
            for i in range(size):
                tc._obs_grid[i] = list(self._obs_grid[i])

        tc._cities_id = [] if hide_info else list(self._cities_id)
        tc._connected_cities = [] if hide_info else list(self._connected_cities)
        tc._tribes_met = [] if hide_info else list(self._tribes_met)
        tc._extra_units = [] if hide_info else list(self._extra_units)

        if hide_info:
            tc._monuments = {}
        else:
            tc._monuments = dict(self._monuments)

        return tc

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def clear_view(
        self, x: int, y: int, radius: int, rnd: _random.Random, board
    ) -> bool:
        size = len(self._obs_grid)
        center = Vector2d(x, y)
        requires_network_update = False

        tiles = center.neighborhood(radius, 0, size)
        tiles.append(center)

        for tile in tiles:
            if not self._obs_grid[tile.x][tile.y]:
                self._obs_grid[tile.x][tile.y] = True
                self._score += cfg.CLEAR_VIEW_POINTS

                terr = board.get_terrain_at(tile.x, tile.y)
                if board.is_road(tile.x, tile.y) or (
                    terr is not None and terr.is_water()
                ):
                    requires_network_update = True

            unit = board.get_unit_at(tile.x, tile.y)
            city = board.get_city_in_borders(tile.x, tile.y)

            if unit is not None:
                self._meet_tribe(rnd, board.get_tribes(), unit.get_tribe_id())
                if board.get_tribe(unit.tribe_id)._obs_grid[tile.x][tile.y]:
                    self._meet_tribe(rnd, board.get_tribes(), self.tribe_id)

            if city is not None:
                self._meet_tribe(rnd, board.get_tribes(), city.get_tribe_id())
                if board.get_tribe(city.tribe_id)._obs_grid[tile.x][tile.y]:
                    self._meet_tribe(rnd, board.get_tribes(), self.tribe_id)

        if (
            not C.PLAY_WITH_FULL_OBS
            and self._monuments.get(BUILDING_TYPE.EYE_OF_GOD)
            is MONUMENT_STATUS.UNAVAILABLE
        ):
            for row in self._obs_grid:
                for val in row:
                    if not val:
                        return requires_network_update
            self._monuments[BUILDING_TYPE.EYE_OF_GOD] = MONUMENT_STATUS.AVAILABLE

        return requires_network_update

    # ------------------------------------------------------------------
    # City management
    # ------------------------------------------------------------------

    def add_city(self, city_id: int) -> None:
        self._cities_id.append(city_id)

    def _remove_city(self, city_id: int) -> None:
        for i, cid in enumerate(self._cities_id):
            if cid == city_id:
                self._cities_id.pop(i)
                return

    def get_cities_id(self) -> list[int]:
        return self._cities_id

    def get_num_cities(self) -> int:
        return len(self._cities_id)

    def controls_capital(self) -> bool:
        return self._capital_id in self._cities_id

    def controls_city(self, city_id: int) -> bool:
        return city_id in self._cities_id

    # ------------------------------------------------------------------
    # Network
    # ------------------------------------------------------------------

    def update_network(self, pathfinder, board, this_tribes_turn: bool) -> None:
        lost_cities: list[int] = []
        added_cities: list[int] = []

        if not self.controls_capital():
            lost_cities.extend(self._connected_cities)
            self._connected_cities.clear()
        elif pathfinder is not None:
            capital = board.get_actor(self._capital_id)

            for city_id in self._cities_id:
                if city_id != self._capital_id:
                    non_capital_city = board.get_actor(city_id)
                    non_capital_pos = non_capital_city.get_position()
                    path_to_city = pathfinder.find_path_to(non_capital_pos)

                    connected_now = path_to_city is not None and len(path_to_city) > 0

                    if city_id in self._connected_cities:
                        if not connected_now:
                            self._drop_city_from_network(non_capital_city)
                            lost_cities.append(city_id)
                    elif connected_now:
                        self._connected_cities.append(city_id)
                        added_cities.append(city_id)

            conn_copy = list(self._connected_cities)
            for city_id in conn_copy:
                if not self.controls_city(city_id):
                    self._drop_city_from_network(board.get_actor(city_id))
                    lost_cities.append(city_id)

            capital_gain = len(added_cities) - len(lost_cities)
            capital.add_population(self, capital_gain)

            if (
                len(self._connected_cities) >= cfg.GRAND_BAZAR_CITIES
                and self._monuments.get(BUILDING_TYPE.GRAND_BAZAR)
                is MONUMENT_STATUS.UNAVAILABLE
            ):
                self._monuments[BUILDING_TYPE.GRAND_BAZAR] = MONUMENT_STATUS.AVAILABLE

        if this_tribes_turn:
            for city_id in added_cities:
                non_capital_city = board.get_actor(city_id)
                non_capital_city.add_population(self, 1)

    def _drop_city_from_network(self, lost_city: City) -> None:
        city_id = lost_city.get_actor_id()
        if city_id in self._connected_cities:
            self._connected_cities.remove(city_id)
        lost_city.add_population(self, -1)

    # ------------------------------------------------------------------
    # Stars
    # ------------------------------------------------------------------

    def add_stars(self, stars: int) -> None:
        self._stars += stars
        if (
            self._stars >= cfg.EMPERORS_TOMB_STARS
            and self._monuments.get(BUILDING_TYPE.EMPERORS_TOMB)
            is MONUMENT_STATUS.UNAVAILABLE
        ):
            self._monuments[BUILDING_TYPE.EMPERORS_TOMB] = MONUMENT_STATUS.AVAILABLE

    def subtract_stars(self, stars: int) -> None:
        self._stars -= stars

    def get_stars(self) -> int:
        return self._stars

    def set_stars(self, stars: int) -> None:
        self._stars = stars

    def can_send_stars(self, num_stars: int) -> bool:
        return self._stars_sent < 30 and num_stars < self._stars and self._stars > 0

    def set_stars_sent(self, num_stars: int) -> None:
        self._stars_sent = num_stars

    def get_stars_sent(self) -> int:
        return self._stars_sent

    def reset_stars_sent(self) -> None:
        self._stars_sent = 0

    # ------------------------------------------------------------------
    # Score
    # ------------------------------------------------------------------

    def add_score(self, score: int) -> None:
        self._score += score

    def subtract_score(self, score: int) -> None:
        self._score -= score

    def get_score(self) -> int:
        return self._score

    def set_score(self, score: int) -> None:
        self._score = score

    def get_reverse_score(self) -> int:
        return -self._score

    # ------------------------------------------------------------------
    # Kills / pacifism
    # ------------------------------------------------------------------

    def add_kill(self) -> None:
        self._n_kills += 1
        if (
            self._n_kills >= cfg.GATE_OF_POWER_KILLS
            and self._monuments.get(BUILDING_TYPE.GATE_OF_POWER)
            is MONUMENT_STATUS.UNAVAILABLE
        ):
            self._monuments[BUILDING_TYPE.GATE_OF_POWER] = MONUMENT_STATUS.AVAILABLE

    def add_pacifist_count(self) -> None:
        if self._tech_tree.is_researched(TECHNOLOGY.MEDITATION):
            self._n_pacifist_count += 1
            if self._n_pacifist_count == cfg.ALTAR_OF_PEACE_TURNS:
                self._monuments[BUILDING_TYPE.ALTAR_OF_PEACE] = (
                    MONUMENT_STATUS.AVAILABLE
                )

    def reset_pacifist_count(self) -> None:
        self._n_pacifist_count = 0

    # ------------------------------------------------------------------
    # Monuments
    # ------------------------------------------------------------------

    def is_monument_buildable(self, building: BUILDING_TYPE) -> bool:
        return self._monuments.get(building) is MONUMENT_STATUS.AVAILABLE

    def monument_is_built(self, building: BUILDING_TYPE) -> None:
        self._monuments[building] = MONUMENT_STATUS.BUILT

    def city_maxed_up(self) -> None:
        if (
            self._monuments.get(BUILDING_TYPE.PARK_OF_FORTUNE)
            is MONUMENT_STATUS.UNAVAILABLE
        ):
            self._monuments[BUILDING_TYPE.PARK_OF_FORTUNE] = MONUMENT_STATUS.AVAILABLE

    def all_researched(self) -> None:
        if (
            self._monuments.get(BUILDING_TYPE.TOWER_OF_WISDOM)
            is MONUMENT_STATUS.UNAVAILABLE
        ):
            self._monuments[BUILDING_TYPE.TOWER_OF_WISDOM] = MONUMENT_STATUS.AVAILABLE

    def get_monuments(self) -> dict:
        return self._monuments

    # ------------------------------------------------------------------
    # Tech tree
    # ------------------------------------------------------------------

    def set_tech_tree(self, tech_tree: TechnologyTree) -> None:
        self._tech_tree = tech_tree

    def get_tech_tree(self) -> TechnologyTree:
        return self._tech_tree

    def get_initial_technology(self) -> Optional[TECHNOLOGY]:
        return self._tribe.get_initial_tech()

    # ------------------------------------------------------------------
    # Units
    # ------------------------------------------------------------------

    def move_all_units(self, units: list[int]) -> None:
        self._extra_units.extend(units)

    def add_extra_unit(self, target: Unit) -> None:
        self._extra_units.append(target.get_actor_id())
        target.set_city_id(-1)

    def remove_extra_unit(self, target: Unit) -> None:
        idx = (
            self._extra_units.index(target.get_actor_id())
            if target.get_actor_id() in self._extra_units
            else -1
        )
        if idx != -1:
            self._extra_units.pop(idx)

    def get_extra_units(self) -> list[int]:
        return self._extra_units

    # ------------------------------------------------------------------
    # Captured / lost city
    # ------------------------------------------------------------------

    def captured_city(self, game_state, captured: City) -> None:
        self.add_city(captured.get_actor_id())
        captured.set_tribe_id(self.tribe_id)
        for building in captured.get_buildings():
            captured.update_building_effects(game_state, building, False, True)

    def lost_city(self, game_state, lost_city: City) -> None:
        self._remove_city(lost_city.get_actor_id())
        for building in lost_city.get_buildings():
            if building.type.is_base() or building.type is BUILDING_TYPE.PORT:
                lost_city.update_building_effects(game_state, building, True, True)

    def manage_loss(self, game_state) -> None:
        self._winner = RESULT.LOSS
        for city_id in self._cities_id:
            city = game_state.get_actor(city_id)
            for unit_id in city.get_units_id():
                unit = game_state.get_actor(unit_id)
                game_state.get_board().remove_unit_from_board(unit)
            city.clear_units()
        for unit_id in self._extra_units:
            unit = game_state.get_actor(unit_id)
            game_state.get_board().remove_unit_from_board(unit)
        self._extra_units.clear()

    # ------------------------------------------------------------------
    # Diplomacy helpers
    # ------------------------------------------------------------------

    def can_build_roads(self) -> bool:
        return (
            self._tech_tree.is_researched(TECHNOLOGY.ROADS)
            and self._stars >= cfg.ROAD_COST
        )

    def get_max_production(self, game_state) -> int:
        total = 0
        for city_id in self._cities_id:
            city = game_state.get_actor(city_id)
            total += city.get_production()
        return total

    def _meet_tribe(self, rnd: _random.Random, tribes: list, tribe_id: int) -> None:
        for met_id in self._tribes_met:
            if tribe_id == met_id or tribe_id == self.tribe_id:
                return
        self._tribes_met.append(tribe_id)

        if not C.PLAY_WITH_FULL_OBS:
            this_tree = self.get_tech_tree()
            met_tree = tribes[tribe_id].get_tech_tree()
            potential = [
                t
                for t in TECHNOLOGY
                if met_tree.is_researched(t) and not this_tree.is_researched(t)
            ]
            if not potential:
                return
            tech = potential[rnd.randint(0, len(potential) - 1)]
            this_tree.do_research(tech)

    # ------------------------------------------------------------------
    # Misc getters / setters
    # ------------------------------------------------------------------

    def get_name(self) -> str:
        return self._tribe.get_name()

    def get_type(self) -> TRIBE_TYPE:
        return self._tribe

    def get_winner(self) -> RESULT:
        return self._winner

    def set_winner(self, winner: RESULT) -> None:
        self._winner = winner

    def get_obs_grid(self) -> list[list[bool]]:
        return self._obs_grid

    def is_visible(self, x: int, y: int) -> bool:
        return self._obs_grid[x][y]

    def set_capital_id(self, capital_id: int) -> None:
        self._capital_id = capital_id

    def get_capital_id(self) -> int:
        return self._capital_id

    def set_position(self, x: int, y: int) -> None:
        self.position = None  # tribes have no position

    def get_position(self):  # type: ignore[override]
        return None

    def get_tribes_met(self) -> list[int]:
        return self._tribes_met

    def get_connected_cities(self) -> list[int]:
        return self._connected_cities

    def get_n_kills(self) -> int:
        return self._n_kills

    def get_n_pacifist_count(self) -> int:
        return self._n_pacifist_count

    def set_has_declared_war(self, val: bool) -> None:
        self._has_declared_war = val

    def get_has_declared_war(self) -> bool:
        return self._has_declared_war

    def get_n_wars_declared(self) -> int:
        return self._n_wars_declared

    def get_n_stars_sent(self) -> int:
        return self._n_stars_sent

    def set_n_stars_sent(self, num_stars: int) -> None:
        self._n_stars_sent = num_stars

    def set_n_wars_declared(self, wars_declared: int) -> None:
        self._n_wars_declared = wars_declared
