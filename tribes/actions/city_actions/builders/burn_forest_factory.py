"BurnForestFactory."
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tribes.actors.city import City
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action
from tribes.utils.vector2d import Vector2d


class BurnForestFactory:
    def compute_action_variants(self, city: City, gs: GameState) -> list[Action]:
        from tribes.actions.city_actions.burn_forest import BurnForest
        actions: list[Action] = []
        tiles = gs.get_board().get_city_tiles(city.actor_id)
        for tile in tiles:
            action = BurnForest(city.actor_id)
            action.set_target_pos(Vector2d(tile.x, tile.y))
            if action.is_feasible(gs):
                actions.append(action)
        return actions
