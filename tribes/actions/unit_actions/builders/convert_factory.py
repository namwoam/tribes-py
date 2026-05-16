"ConvertFactory."

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tribes.actors.units.unit import Unit
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action


class ConvertFactory:
    def compute_action_variants(self, unit: Unit, gs: GameState) -> list[Action]:
        from tribes.actions.unit_actions.convert import Convert

        converts: list[Action] = []
        if not unit.can_attack():
            return converts
        board = gs.get_board()
        for tile in unit.get_position().neighborhood(unit.RANGE, 0, board.get_size()):
            target = board.get_unit_at(tile.x, tile.y)
            if target is not None and target.tribe_id != unit.tribe_id:
                c = Convert(unit.actor_id)
                c.set_target_id(target.actor_id)
                if c.is_feasible(gs):
                    converts.append(c)
        return converts
