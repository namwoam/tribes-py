"UpgradeFactory."

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tribes.actors.units.unit import Unit
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action
from tribes.types import ACTION, UNIT as UNIT_TYPE


class UpgradeFactory:
    def compute_action_variants(self, unit: Unit, gs: GameState) -> list[Action]:
        from tribes.actions.unit_actions.upgrade import Upgrade

        actions: list[Action] = []
        action_type = None
        if unit.get_type() is UNIT_TYPE.BOAT:
            action_type = ACTION.UPGRADE_BOAT
        elif unit.get_type() is UNIT_TYPE.SHIP:
            action_type = ACTION.UPGRADE_SHIP

        if action_type is None:
            return actions

        action = Upgrade(action_type, unit.actor_id)
        if action.is_feasible(gs):
            actions.append(action)
        return actions
