"EndTurn action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.tribe_actions.tribe_action import TribeAction
from tribes.types import ACTION

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class EndTurn(TribeAction):
    def __init__(self, tribe_id: int = -1) -> None:
        super().__init__(ACTION.END_TURN)
        self.tribe_id = tribe_id

    def is_feasible(self, gs: GameState) -> bool:
        tribe = gs.get_tribe(self.tribe_id)
        return gs.can_end_turn(tribe.tribe_id)

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        gs.set_end_turn(True)
        return True

    def copy(self) -> EndTurn:
        return EndTurn(self.tribe_id)

    def __str__(self) -> str:
        return f"END_TURN by tribe {self.tribe_id}"
