"BuildFactory."
from __future__ import annotations
from typing import TYPE_CHECKING
from tribes.types import BUILDING
if TYPE_CHECKING:
    from tribes.actors.city import City
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action


class BuildFactory:
    def compute_action_variants(self, city: City, gs: GameState) -> list[Action]:
        from tribes.actions.city_actions.build import Build
        actions: list[Action] = []
        board = gs.get_board()
        tiles = board.get_city_tiles(city.actor_id)
        for tile in tiles:
            for building in BUILDING:
                if board.get_building_at(tile.x, tile.y) is None:
                    action = Build(city.actor_id)
                    action.set_building_type(building)
                    action.set_target_pos(tile.copy())
                    if action.is_feasible(gs):
                        actions.append(action)
        return actions
