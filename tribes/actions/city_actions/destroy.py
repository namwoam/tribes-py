"Destroy action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.city_actions.city_action import CityAction
from tribes.types import ACTION, TECHNOLOGY, BUILDING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Destroy(CityAction):
    def __init__(self, city_id: int) -> None:
        super().__init__(ACTION.DESTROY)
        self.city_id = city_id

    def is_feasible(self, gs: GameState) -> bool:
        tp = self.target_pos
        if tp is None:
            return False
        city = gs.get_actor(self.city_id)
        board = gs.get_board()
        if board.get_building_at(tp.x, tp.y) is None:
            return False
        building_to_remove = city.get_building(tp.x, tp.y)
        if building_to_remove is None or building_to_remove.type is None:
            return False
        if board.get_city_id_at(tp.x, tp.y) != self.city_id:
            return False
        return gs.get_tribe(city.tribe_id).get_tech_tree().is_researched(TECHNOLOGY.CONSTRUCTION)

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        city = gs.get_actor(self.city_id)
        tp = self.target_pos
        board = gs.get_board()
        building_to_remove = city.get_building(tp.x, tp.y)
        board.set_building_at(tp.x, tp.y, None)
        if building_to_remove.type is BUILDING.PORT:
            board.destroy_port(tp.x, tp.y)
        city.remove_building(gs, building_to_remove)
        return True

    def copy(self) -> Destroy:
        d = Destroy(self.city_id)
        if self.target_pos is not None:
            d.target_pos = self.target_pos.copy()
        return d

    def __str__(self) -> str:
        return f"DESTROY by city {self.city_id} at {self.target_pos}"
