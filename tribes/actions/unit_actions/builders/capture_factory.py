"CaptureFactory."

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tribes.actors.units.unit import Unit
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action
from tribes.types import TERRAIN


class CaptureFactory:
    def compute_action_variants(self, unit: Unit, gs: GameState) -> list[Action]:
        from tribes.actions.unit_actions.capture import Capture

        captures: list[Action] = []
        if not unit.is_fresh():
            return captures
        t = gs.get_board().get_terrain_at(unit.get_position().x, unit.get_position().y)
        if t is TERRAIN.VILLAGE:
            capture = Capture(unit.actor_id)
            capture.set_target_city(-1)
            capture.set_capture_type(t)
            if capture.is_feasible(gs):
                captures.append(capture)
        elif t is TERRAIN.CITY:
            board = gs.get_board()
            c = board.get_city_in_borders(unit.get_position().x, unit.get_position().y)
            if c is not None:
                capture = Capture(unit.actor_id)
                capture.set_target_city(c.actor_id)
                capture.set_capture_type(t)
                if capture.is_feasible(gs):
                    captures.append(capture)
        return captures
