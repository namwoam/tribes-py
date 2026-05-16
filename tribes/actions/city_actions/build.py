"Build action + command, ported from Build.java + BuildCommand.java."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.city_actions.city_action import CityAction
from tribes.types import ACTION, BUILDING, TECHNOLOGY, RESOURCE, TERRAIN

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.utils.vector2d import Vector2d
    from tribes.game.game_state import GameState


class Build(CityAction):
    """Build a building in a city tile."""

    def __init__(self, city_id: int) -> None:
        super().__init__(ACTION.BUILD)
        self.city_id = city_id
        self._building_type: Optional[BUILDING] = None

    def set_building_type(self, bt: BUILDING) -> None:
        self._building_type = bt

    def get_building_type(self) -> Optional[BUILDING]:
        return self._building_type

    def is_feasible(self, gs: GameState) -> bool:
        bt = self._building_type
        if bt is None:
            return False
        non_unique = (BUILDING.PORT, BUILDING.FARM, BUILDING.MINE, BUILDING.LUMBER_HUT,
                      BUILDING.TEMPLE, BUILDING.WATER_TEMPLE, BUILDING.MOUNTAIN_TEMPLE,
                      BUILDING.FOREST_TEMPLE)
        unique = (BUILDING.SAWMILL, BUILDING.CUSTOMS_HOUSE, BUILDING.WINDMILL, BUILDING.FORGE)
        monuments = (BUILDING.ALTAR_OF_PEACE, BUILDING.EMPERORS_TOMB, BUILDING.EYE_OF_GOD,
                     BUILDING.GATE_OF_POWER, BUILDING.PARK_OF_FORTUNE,
                     BUILDING.TOWER_OF_WISDOM, BUILDING.GRAND_BAZAR)
        if bt in non_unique:
            return self._is_buildable(gs, bt.get_cost(), False)
        if bt in unique:
            return self._is_buildable(gs, bt.get_cost(), True)
        if bt in monuments:
            if not self._is_buildable(gs, bt.get_cost(), False):
                return False
            city = gs.get_actor(self.city_id)
            tribe = gs.get_tribe(city.tribe_id)
            return tribe.is_monument_buildable(bt)
        return False

    def _is_buildable(self, gs: GameState, cost: int, check_unique: bool) -> bool:
        city = gs.get_actor(self.city_id)
        tribe = gs.get_tribe(city.tribe_id)
        board = gs.get_board()
        tech_tree = tribe.get_tech_tree()

        if cost > 0 and tribe.get_stars() < cost:
            return False
        tech_req = self._building_type.get_technology_requirement()
        if tech_req is not None and not tech_tree.is_researched(tech_req):
            return False
        tp = self.target_pos
        if tp is None:
            return False
        ter = board.get_terrain_at(tp.x, tp.y)
        if ter not in self._building_type.get_terrain_requirements():
            return False
        res_needed = self._building_type.get_resource_constraint()
        if res_needed is not None:
            res_at = board.get_resource_at(tp.x, tp.y)
            if res_at is None or res_needed is not res_at:
                return False
        adj_needed = self._building_type.get_adjacency_constraint()
        if adj_needed is not None:
            adj_found = False
            for adj_pos in tp.neighborhood(1, 0, board.get_size()):
                if board.get_building_at(adj_pos.x, adj_pos.y) is adj_needed:
                    adj_found = True
                    break
            if not adj_found:
                return False
        if check_unique:
            for tile in board.get_city_tiles(self.city_id):
                if board.get_building_at(tile.x, tile.y) is self._building_type:
                    return False
        return True

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        city = gs.get_actor(self.city_id)
        tribe = gs.get_tribe(city.tribe_id)
        board = gs.get_board()
        tp = self.target_pos
        bt = self._building_type

        tribe.subtract_stars(bt.get_cost())
        board.set_building_at(tp.x, tp.y, bt)
        board.set_resource_at(tp.x, tp.y, None)

        from tribes.actors.building import Building, Temple
        if bt.is_temple():
            city.add_building(gs, Temple(tp.x, tp.y, bt, self.city_id))
        else:
            city.add_building(gs, Building(tp.x, tp.y, bt, self.city_id))

        if bt is BUILDING.PORT:
            board.build_port(tp.x, tp.y)
        if bt.is_monument():
            tribe.monument_is_built(bt)
        if bt is BUILDING.LUMBER_HUT:
            board.set_terrain_at(tp.x, tp.y, TERRAIN.PLAIN)

        return True

    def copy(self) -> Build:
        b = Build(self.city_id)
        b._building_type = self._building_type
        if self.target_pos is not None:
            b.target_pos = self.target_pos.copy()
        return b

    def __str__(self) -> str:
        return f"BUILD by city {self.city_id} at {self.target_pos}: {self._building_type}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Build):
            return False
        return super().__eq__(other) and self._building_type == other._building_type
