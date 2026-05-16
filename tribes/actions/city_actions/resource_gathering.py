"ResourceGathering action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.city_actions.city_action import CityAction
from tribes.types import ACTION, RESOURCE, TECHNOLOGY

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class ResourceGathering(CityAction):
    def __init__(self, city_id: int) -> None:
        super().__init__(ACTION.RESOURCE_GATHERING)
        self.city_id = city_id
        self._resource: Optional[RESOURCE] = None

    def set_resource(self, resource: RESOURCE) -> None:
        self._resource = resource

    def get_resource(self) -> Optional[RESOURCE]:
        return self._resource

    def is_feasible(self, gs: GameState) -> bool:
        tp = self.target_pos
        if tp is None or self._resource is None:
            return False
        city = gs.get_actor(self.city_id)
        board = gs.get_board()
        t = board.get_tribe(city.tribe_id)
        if (board.get_resource_at(tp.x, tp.y) is not self._resource
                or t.get_stars() < self._resource.get_cost()):
            return False
        tt = t.get_tech_tree()
        r = self._resource
        if r is RESOURCE.ANIMAL:
            return tt.is_researched(TECHNOLOGY.HUNTING)
        if r is RESOURCE.FISH:
            return tt.is_researched(TECHNOLOGY.FISHING)
        if r is RESOURCE.WHALES:
            return tt.is_researched(TECHNOLOGY.WHALING)
        if r is RESOURCE.FRUIT:
            return tt.is_researched(TECHNOLOGY.ORGANIZATION)
        return False

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        city = gs.get_actor(self.city_id)
        tp = self.target_pos
        gs.get_board().set_resource_at(tp.x, tp.y, None)
        tribe = gs.get_tribe(city.tribe_id)
        r = self._resource
        tribe.subtract_stars(r.get_cost())
        if r in (RESOURCE.FISH, RESOURCE.ANIMAL, RESOURCE.FRUIT):
            city.add_population(tribe, r.get_bonus())
            return True
        if r is RESOURCE.WHALES:
            tribe.add_stars(r.get_bonus())
            return True
        return False

    def copy(self) -> ResourceGathering:
        rg = ResourceGathering(self.city_id)
        rg._resource = self._resource
        if self.target_pos is not None:
            rg.target_pos = self.target_pos.copy()
        return rg

    def __str__(self) -> str:
        return f"RESOURCE_GATHERED by city {self.city_id}: {self._resource}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResourceGathering):
            return False
        return super().__eq__(other) and self._resource == other._resource
