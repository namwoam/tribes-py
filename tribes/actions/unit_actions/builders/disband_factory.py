"DisbandFactory."

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tribes.actors.units.unit import Unit
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action


class DisbandFactory:
    def compute_action_variants(self, unit: Unit, gs: GameState) -> list[Action]:
        from tribes.actions.unit_actions.disband import Disband

        actions: list[Action] = []
        action = Disband(unit.actor_id)
        if action.is_feasible(gs):
            actions.append(action)
        return actions
