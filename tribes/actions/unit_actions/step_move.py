"StepMove NeighbourHelper for unit pathfinding, ported from StepMove.java."
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from tribes.utils.path_node import PathNode
from tribes.utils.vector2d import Vector2d
from tribes.types import TERRAIN, BUILDING, UNIT as UNIT_TYPE

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState
    from tribes.actors.units.unit import Unit


class StepMove:
    """Implements movement rules for unit pathfinding."""

    def __init__(self, gs: GameState, unit: Unit) -> None:
        self._gs = gs
        self._unit = unit

    def get_neighbours(self, frm: Vector2d, cost_from: float) -> list[PathNode]:
        neighbours: list[PathNode] = []
        if cost_from == self._unit.MOV:
            return neighbours

        board = self._gs.get_board()
        unit = self._unit
        on_road = False

        if (board.is_road(frm.x, frm.y)
                or board.get_terrain_at(frm.x, frm.y) is TERRAIN.CITY):
            city_id = board.get_city_id_at(frm.x, frm.y)
            if city_id == -1 or board.get_tribe(unit.tribe_id).controls_city(city_id):
                on_road = True

        for tile in frm.neighborhood(1, 0, board.get_size()):
            terrain = board.get_terrain_at(tile.x, tile.y)
            step_cost = 0.0
            zone_of_control = False

            # Can't move to tiles with non-friendly units
            other_unit = board.get_unit_at(tile.x, tile.y)
            if other_unit is not None and other_unit.tribe_id != unit.tribe_id:
                continue

            # Zone of control check
            for tile_adj in tile.neighborhood(1, 0, board.get_size()):
                u = board.get_unit_at(tile_adj.x, tile_adj.y)
                if u is not None and u.tribe_id != unit.tribe_id:
                    zone_of_control = True

            # Must be visible
            if not self._gs.get_tribe(unit.tribe_id).is_visible(tile.x, tile.y):
                continue

            # Research / traversal constraints
            if not board.traversable(tile.x, tile.y, unit.tribe_id):
                continue

            # Mind benders can't enter enemy city tiles
            if (unit.get_type() is UNIT_TYPE.MIND_BENDER
                    and terrain is TERRAIN.CITY):
                target_city = board.get_actor(board.get_city_id_at(tile.x, tile.y))
                if target_city is not None and target_city.tribe_id != unit.tribe_id:
                    continue

            if unit.get_type().is_water_unit():
                if terrain in (TERRAIN.CITY, TERRAIN.PLAIN, TERRAIN.FOREST,
                               TERRAIN.VILLAGE, TERRAIN.MOUNTAIN):
                    step_cost = (unit.MOV - cost_from) if cost_from < unit.MOV else unit.MOV
                elif terrain in (TERRAIN.FOG, TERRAIN.DEEP_WATER, TERRAIN.SHALLOW_WATER):
                    step_cost = 1.0
                else:
                    step_cost = 1.0
            else:
                if terrain in (TERRAIN.SHALLOW_WATER, TERRAIN.DEEP_WATER):
                    if board.get_building_at(tile.x, tile.y) is BUILDING.PORT:
                        step_cost = (unit.MOV - cost_from) if cost_from < unit.MOV else unit.MOV
                    else:
                        continue
                elif terrain in (TERRAIN.FOG, TERRAIN.PLAIN, TERRAIN.CITY, TERRAIN.VILLAGE):
                    step_cost = 1.0
                elif terrain in (TERRAIN.FOREST, TERRAIN.MOUNTAIN):
                    step_cost = (unit.MOV - cost_from) if cost_from < unit.MOV else unit.MOV
                else:
                    step_cost = 1.0

                if on_road and (board.is_road(tile.x, tile.y)
                                or board.get_terrain_at(tile.x, tile.y) is TERRAIN.CITY):
                    city_id2 = board.get_city_id_at(frm.x, frm.y)
                    if city_id2 == -1 or board.get_tribe(unit.tribe_id).controls_city(city_id2):
                        step_cost = max(0.5, step_cost / 2.0)

            if zone_of_control:
                step_cost = (unit.MOV - cost_from) if cost_from < unit.MOV else unit.MOV
                if cost_from + step_cost <= unit.MOV:
                    neighbours.append(PathNode(tile, step_cost))
            elif math.floor(cost_from + step_cost) <= unit.MOV:
                neighbours.append(PathNode(tile, step_cost))

        return neighbours

    def add_jump_link(self, frm: Vector2d, to: Vector2d, reverse: bool) -> None:
        pass  # no jump links
