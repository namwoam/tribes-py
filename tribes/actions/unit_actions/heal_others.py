"HealOthers action + command."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, UNIT as UNIT_TYPE, TURN_STATUS
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState
    from tribes.actors.units.unit import Unit


class HealOthers(UnitAction):
    def __init__(self, unit_id: int) -> None:
        super().__init__(ACTION.HEAL_OTHERS)
        self.unit_id = unit_id

    def is_feasible(self, gs: GameState) -> bool:
        board = gs.get_board()
        unit = gs.get_actor(self.unit_id)
        if unit.get_type() is not UNIT_TYPE.MIND_BENDER or not unit.can_attack():
            return False
        for tile in unit.get_position().neighborhood(unit.RANGE, 0, board.get_size()):
            u = board.get_unit_at(tile.x, tile.y)
            if self._can_be_healed(unit, u):
                return True
        return False

    def _can_be_healed(self, healer: Unit, target: Unit) -> bool:
        if target is not None and target.tribe_id == healer.tribe_id:
            return (
                target.get_current_hp() < target.get_max_hp()
                and target.tribe_id == healer.tribe_id
            )
        return False

    def get_targets(self, gs: GameState) -> list[Unit]:
        targets = []
        unit = gs.get_actor(self.unit_id)
        for tile in unit.get_position().neighborhood(
            unit.RANGE, 0, gs.get_board().get_size()
        ):
            u = gs.get_board().get_unit_at(tile.x, tile.y)
            if self._can_be_healed(unit, u):
                targets.append(u)
        return targets

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        unit = gs.get_actor(self.unit_id)
        targets = self.get_targets(gs)
        for target in targets:
            target.set_current_hp(
                min(target.get_current_hp() + cfg.MINDBENDER_HEAL, target.get_max_hp())
            )
        unit.transition_to_status(TURN_STATUS.ATTACKED)
        return True

    def copy(self) -> HealOthers:
        return HealOthers(self.unit_id)

    def __str__(self) -> str:
        return f"HEAL by unit {self.unit_id}"
