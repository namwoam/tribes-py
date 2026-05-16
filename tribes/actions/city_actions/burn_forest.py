"BurnForest action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.city_actions.city_action import CityAction
from tribes.types import ACTION, TERRAIN, RESOURCE, TECHNOLOGY
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class BurnForest(CityAction):
    def __init__(self, city_id: int) -> None:
        super().__init__(ACTION.BURN_FOREST)
        self.city_id = city_id

    def is_feasible(self, gs: GameState) -> bool:
        city = gs.get_actor(self.city_id)
        board = gs.get_board()
        tp = self.target_pos
        if tp is None:
            return False
        if board.get_terrain_at(tp.x, tp.y) is not TERRAIN.FOREST:
            return False
        if board.get_city_id_at(tp.x, tp.y) != self.city_id:
            return False
        t = gs.get_tribe(city.tribe_id)
        if t.get_stars() < cfg.BURN_FOREST_COST:
            return False
        return t.get_tech_tree().is_researched(TECHNOLOGY.CHIVALRY)

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        city = gs.get_actor(self.city_id)
        tp = self.target_pos
        board = gs.get_board()
        t = gs.get_tribe(city.tribe_id)
        board.set_terrain_at(tp.x, tp.y, TERRAIN.PLAIN)
        board.set_resource_at(tp.x, tp.y, RESOURCE.CROPS)
        t.subtract_stars(cfg.BURN_FOREST_COST)
        return True

    def copy(self) -> BurnForest:
        b = BurnForest(self.city_id)
        if self.target_pos is not None:
            b.target_pos = self.target_pos.copy()
        return b

    def __str__(self) -> str:
        return f"BURN_FOREST by city {self.city_id} at {self.target_pos}"
