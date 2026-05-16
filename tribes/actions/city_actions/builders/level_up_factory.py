"LevelUpFactory."
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tribes.actors.city import City
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action
from tribes.types import CITY_LEVEL_UP


class LevelUpFactory:
    def compute_action_variants(self, city: City, gs: GameState) -> list[Action]:
        from tribes.actions.city_actions.level_up import LevelUp
        actions: list[Action] = []
        bonuses = CITY_LEVEL_UP.get_actions(city.get_level())
        for bonus in bonuses:
            lu = LevelUp(city.actor_id)
            lu.set_bonus(bonus)
            lu.set_target_pos(city.get_position().copy())
            if lu.is_feasible(gs):
                actions.append(lu)
        return actions
