"ActionCommand interface (kept for reference, not used directly)."
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tribes.actions.action import Action
    from tribes.game.game_state import GameState


class ActionCommand(ABC):
    @abstractmethod
    def execute(self, a: Action, gs: GameState) -> bool: ...
