"Abstract Agent base class, ported from Agent.java."
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from tribes.types import ACTION

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.actions.action import Action
    from tribes.game.game_state import GameState


class Agent(ABC):
    """Abstract base for all AI/human agents."""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.player_id: int = -1
        self.all_player_ids: list[int] = []

    @abstractmethod
    def act(self, gs: GameState) -> Action:
        """Return the action to play in the given game state."""
        ...

    def result(self, gs: GameState, reward: float) -> None:
        """Called at end of game; agents may override for analysis."""

    def set_player_ids(self, player_id: int, all_ids: list[int]) -> None:
        self.player_id = player_id
        self.all_player_ids = list(all_ids)

    def get_player_id(self) -> int:
        return self.player_id

    @abstractmethod
    def copy(self) -> Agent:
        ...

    # ------------------------------------------------------------------
    # Helper: collect "good" actions (no Destroy / Disband)
    # ------------------------------------------------------------------

    def _all_good_actions(self, gs: GameState) -> list[Action]:
        from tribes.actions.action import Action as ActionBase
        all_actions: list[ActionBase] = []
        for act in gs.get_all_city_actions():
            if act.action_type is not ACTION.DESTROY:
                all_actions.append(act)
        for act in gs.get_all_unit_actions():
            if act.action_type is not ACTION.DISBAND:
                all_actions.append(act)
        all_actions.extend(gs.get_tribe_actions())
        return all_actions
