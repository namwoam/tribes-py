"Spawn action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.city_actions.city_action import CityAction
from tribes.types import ACTION, UNIT as UNIT_TYPE
from tribes.utils.vector2d import Vector2d

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Spawn(CityAction):
    def __init__(self, city_id: int) -> None:
        super().__init__(ACTION.SPAWN)
        self.city_id = city_id
        self._unit_type: Optional[UNIT_TYPE] = None

    def set_unit_type(self, ut: UNIT_TYPE) -> None:
        self._unit_type = ut

    def get_unit_type(self) -> Optional[UNIT_TYPE]:
        return self._unit_type

    def is_feasible(self, gs: GameState) -> bool:
        if self._unit_type is None:
            return False
        city = gs.get_actor(self.city_id)
        t = gs.get_tribe(city.tribe_id)

        if not self._unit_type.spawnable():
            return False
        if t.get_stars() < self._unit_type.get_cost():
            return False
        if not city.can_add_unit():
            return False
        city_pos = city.get_position()
        if gs.get_board().get_unit_at(city_pos.x, city_pos.y) is not None:
            return False
        tech = self._unit_type.get_technology_requirement()
        return tech is None or t.get_tech_tree().is_researched(tech)

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        city = gs.get_actor(self.city_id)
        city_pos = city.get_position()
        ut = self._unit_type
        new_unit = UNIT_TYPE.create_unit(
            Vector2d(city_pos.x, city_pos.y), 0, False,
            city.actor_id, city.tribe_id, ut)
        gs.get_board().add_unit(city, new_unit)
        tribe = gs.get_tribe(city.tribe_id)
        tribe.subtract_stars(ut.get_cost())
        tribe.add_score(ut.get_points())
        return True

    def copy(self) -> Spawn:
        s = Spawn(self.city_id)
        s._unit_type = self._unit_type
        if self.target_pos is not None:
            s.target_pos = self.target_pos.copy()
        return s

    def __str__(self) -> str:
        return f"SPAWN by city {self.city_id}: {self._unit_type}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Spawn):
            return False
        return super().__eq__(other) and self._unit_type == other._unit_type
