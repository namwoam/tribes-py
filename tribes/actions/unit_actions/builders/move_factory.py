"MoveFactory."
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tribes.actors.units.unit import Unit
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action
from tribes.utils.pathfinder import Pathfinder


class MoveFactory:
    def compute_action_variants(self, unit: Unit, gs: GameState) -> list[Action]:
        from tribes.actions.unit_actions.move import Move
        from tribes.actions.unit_actions.step_move import StepMove
        moves: list[Action] = []
        if not unit.can_move():
            return moves
        tp = Pathfinder(unit.get_position(), StepMove(gs, unit))
        for tile in tp.find_paths():
            if gs.get_board().get_unit_at(tile.get_x(), tile.get_y()) is None:
                action = Move(unit.actor_id)
                action.set_destination(tile.get_position())
                moves.append(action)
        return moves
