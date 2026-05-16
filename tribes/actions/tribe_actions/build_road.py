"BuildRoad action + command."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.tribe_actions.tribe_action import TribeAction
from tribes.types import ACTION
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.utils.vector2d import Vector2d
    from tribes.game.game_state import GameState


class BuildRoad(TribeAction):
    def __init__(self, tribe_id: int) -> None:
        super().__init__(ACTION.BUILD_ROAD)
        self.tribe_id = tribe_id
        self._position: Optional[Vector2d] = None

    def set_position(self, pos: Vector2d) -> None:
        self._position = pos.copy()

    def get_position(self) -> Optional[Vector2d]:
        return self._position

    def is_feasible(self, gs: GameState) -> bool:
        tribe = gs.get_tribe(self.tribe_id)
        if not tribe.can_build_roads():
            return False
        if self._position is None:
            return False
        return gs.get_board().can_build_road_at(
            self.tribe_id, self._position.x, self._position.y
        )

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        tribe = gs.get_tribe(self.tribe_id)
        tribe.subtract_stars(cfg.ROAD_COST)
        gs.get_board().add_road(self._position.x, self._position.y)
        return True

    def copy(self) -> BuildRoad:
        br = BuildRoad(self.tribe_id)
        if self._position is not None:
            br._position = self._position.copy()
        return br

    def __str__(self) -> str:
        return f"BUILD_ROAD by tribe {self.tribe_id} at {self._position}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BuildRoad):
            return False
        return super().__eq__(other) and self._position == other._position
