"DoNothingAgent: always plays EndTurn."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.players.agent import Agent
from tribes.actions.tribe_actions.end_turn import EndTurn

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class DoNothingAgent(Agent):
    def __init__(self, seed: int) -> None:
        super().__init__(seed)

    def act(self, gs: GameState) -> EndTurn:
        return EndTurn(gs.get_active_tribe_id())

    def copy(self) -> DoNothingAgent:
        return DoNothingAgent(self.seed)
