"TribeAction base class."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.action import Action
from tribes.types import ACTION

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class TribeAction(Action):
    def __init__(self, action_type: ACTION) -> None:
        super().__init__(action_type)
        self.tribe_id: int = -1

    def set_tribe_id(self, tribe_id: int) -> None:
        self.tribe_id = tribe_id

    def get_tribe_id(self) -> int:
        return self.tribe_id

    def is_feasible(self, gs: GameState) -> bool:
        return False

    def execute(self, gs: GameState) -> bool:
        return False

    def copy(self) -> TribeAction:
        return TribeAction(self.action_type)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TribeAction):
            return False
        return self.tribe_id == other.tribe_id and self.action_type == other.action_type
