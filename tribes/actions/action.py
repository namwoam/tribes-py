"Abstract Action base class, ported from Action.java."

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from tribes.types import ACTION

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Action(ABC):
    """Abstract base for all actions."""

    def __init__(self, action_type: ACTION) -> None:
        self.action_type: ACTION = action_type

    def get_action_type(self) -> ACTION:
        return self.action_type

    @abstractmethod
    def is_feasible(self, gs: GameState) -> bool:
        """Return True if the action can be executed in the given game state."""
        ...

    @abstractmethod
    def execute(self, gs: GameState) -> bool:
        """Execute this action on the game state. Returns True if executed."""
        ...

    @abstractmethod
    def copy(self) -> Action:
        """Return a deep copy of this action."""
        ...
