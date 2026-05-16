"ResourceGatheringFactory."

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tribes.actors.city import City
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action
from tribes.utils.vector2d import Vector2d


class ResourceGatheringFactory:
    def compute_action_variants(self, city: City, gs: GameState) -> list[Action]:
        from tribes.actions.city_actions.resource_gathering import ResourceGathering

        actions: list[Action] = []
        board = gs.get_board()
        city_id = city.actor_id
        for pos in board.get_city_tiles(city_id):
            r = board.get_resource_at(pos.x, pos.y)
            if r is None:
                continue
            action = ResourceGathering(city_id)
            action.set_resource(r)
            action.set_target_pos(Vector2d(pos.x, pos.y))
            if action.is_feasible(gs):
                actions.append(action)
        return actions
