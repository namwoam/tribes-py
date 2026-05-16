"SpawnFactory."
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tribes.actors.city import City
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action
from tribes.types import UNIT as UNIT_TYPE


class SpawnFactory:
    def compute_action_variants(self, city: City, gs: GameState) -> list[Action]:
        from tribes.actions.city_actions.spawn import Spawn
        actions: list[Action] = []
        for unit in UNIT_TYPE:
            action = Spawn(city.actor_id)
            action.set_unit_type(unit)
            action.set_target_pos(city.get_position().copy())
            if action.is_feasible(gs):
                actions.append(action)
        return actions
