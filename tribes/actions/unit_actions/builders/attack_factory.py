"AttackFactory."

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tribes.actors.units.unit import Unit
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action


class AttackFactory:
    def compute_action_variants(self, unit: Unit, gs: GameState) -> list[Action]:
        from tribes.actions.unit_actions.attack import Attack

        attacks: list[Action] = []
        if not unit.can_attack():
            return attacks
        board = gs.get_board()
        position = unit.get_position()
        for tile in position.neighborhood(unit.RANGE, 0, board.get_size()):
            other = board.get_unit_at(tile.x, tile.y)
            if other is not None and other.tribe_id != unit.tribe_id:
                a = Attack(unit.actor_id)
                a.set_target_id(other.actor_id)
                if a.is_feasible(gs):
                    attacks.append(a)
        return attacks
