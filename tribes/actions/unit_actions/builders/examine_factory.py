"ExamineFactory."

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tribes.actors.units.unit import Unit
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action


class ExamineFactory:
    def compute_action_variants(self, unit: Unit, gs: GameState) -> list[Action]:
        from tribes.actions.unit_actions.examine import Examine

        actions: list[Action] = []
        ex = Examine(unit.actor_id)
        if ex.is_feasible(gs):
            actions.append(ex)
        return actions
