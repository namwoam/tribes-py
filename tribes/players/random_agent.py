"RandomAgent: picks a uniformly random available action."
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from tribes.players.agent import Agent

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.actions.action import Action
    from tribes.game.game_state import GameState


class RandomAgent(Agent):
    def __init__(self, seed: int) -> None:
        super().__init__(seed)
        self._rnd = random.Random(seed)

    def act(self, gs: GameState) -> Action:
        all_actions = gs.get_all_available_actions()
        return self._rnd.choice(all_actions)

    def copy(self) -> RandomAgent:
        return RandomAgent(self.seed)
