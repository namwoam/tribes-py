"LevelLoader — parses CSV level files and builds Board, ported from LevelLoader.java."

from __future__ import annotations

import logging
import random as _random

from tribes.types import TERRAIN, RESOURCE, TRIBE as TRIBE_TYPE, UNIT as UNIT_TYPE
from tribes.utils.vector2d import Vector2d
from tribes import config as cfg

logger = logging.getLogger(__name__)


class LevelLoader:
    """Parses CSV-format level files and returns a Board."""

    def __init__(self) -> None:
        self._width = 0
        self._height = 0

    def build_level(self, lines: list[str], rnd: _random.Random):
        from tribes.game.board import Board
        from tribes.actors.city import City

        self._height = len(lines)
        self._width = len(lines)

        tribes = self._extract_tribes(lines)
        board = Board()

        tribe_counter = 0
        num_tribes = len(tribes)

        board.init(self._width, tribes)

        for i in range(self._height):
            line = lines[i]
            tile_tokens = line.split(",")
            for j, token in enumerate(tile_tokens):
                parts = token.strip().split(":")
                terrain_char = parts[0][0]

                if terrain_char == TERRAIN.CITY.get_map_char():
                    tribe_type_key = int(parts[1])
                    tribe_id = -1
                    for t in tribes:
                        if t.get_type().get_key() == tribe_type_key:
                            tribe_id = t.tribe_id
                            break

                    if tribe_counter == num_tribes:
                        # extra city -> village
                        terrain_char = TERRAIN.VILLAGE.get_map_char()
                    else:
                        c = City(i, j, tribe_id)
                        c.set_capital(True)

                        # Luxidoor special case
                        if tribes[tribe_id].get_name() == "Luxidoor":
                            c.level_up()
                            c.level_up()
                            c.set_walls(True)
                            c.set_population(0)

                        board.add_city_to_tribe(c, rnd)
                        tribes[tribe_id].add_score(cfg.CITY_CENTRE_POINTS)

                        unit_type = tribes[tribe_id].get_type().get_starting_unit()
                        unit = UNIT_TYPE.create_unit(
                            Vector2d(i, j), 0, False, c.actor_id, tribe_id, unit_type
                        )
                        board.add_unit(c, unit)
                        tribes[tribe_id].add_score(unit_type.get_points())

                        board.assign_city_tiles(c, c.get_bound())
                        tribe_counter += 1

                board.set_terrain_at(i, j, TERRAIN.get_type(terrain_char))

                if len(parts) == 2 and len(parts[1]) > 0:
                    resource_char = parts[1][0]
                    res = RESOURCE.get_type(resource_char)
                    if res is not None:
                        board.set_resource_at(i, j, res)

        return board

    def _extract_tribes(self, lines: list[str]):
        from tribes.actors.tribe import Tribe

        tribes_list: list[TRIBE_TYPE] = []
        for i in range(self._height):
            line = lines[i]
            tile_tokens = line.split(",")
            for token in tile_tokens:
                parts = token.strip().split(":")
                terrain_char = parts[0][0]
                is_city = terrain_char == TERRAIN.CITY.get_map_char()
                if is_city:
                    tribe_key = int(parts[1])
                    tribes_list.append(TRIBE_TYPE.get_type_by_key(tribe_key))

        result: list[Tribe] = []
        for tr_type in tribes_list:
            result.append(Tribe(tr_type))
        return result
