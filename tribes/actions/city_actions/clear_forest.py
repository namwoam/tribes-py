"ClearForest action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.city_actions.city_action import CityAction
from tribes.types import ACTION, TERRAIN, TECHNOLOGY
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class ClearForest(CityAction):
    def __init__(self, city_id: int) -> None:
        super().__init__(ACTION.CLEAR_FOREST)
        self.city_id = city_id

    def is_feasible(self, gs: GameState) -> bool:
        tp = self.target_pos
        if tp is None:
            return False
        board = gs.get_board()
        if board.get_terrain_at(tp.x, tp.y) is not TERRAIN.FOREST:
            return False
        if board.get_city_id_at(tp.x, tp.y) != self.city_id:
            return False
        city = gs.get_actor(self.city_id)
        return gs.get_tribe(city.tribe_id).get_tech_tree().is_researched(TECHNOLOGY.FORESTRY)

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        city = gs.get_actor(self.city_id)
        tp = self.target_pos
        gs.get_board().set_terrain_at(tp.x, tp.y, TERRAIN.PLAIN)
        gs.get_tribe(city.tribe_id).add_stars(cfg.CLEAR_FOREST_STAR)
        return True

    def copy(self) -> ClearForest:
        c = ClearForest(self.city_id)
        if self.target_pos is not None:
            c.target_pos = self.target_pos.copy()
        return c

    def __str__(self) -> str:
        return f"CLEAR_FOREST by city {self.city_id} at {self.target_pos}"
