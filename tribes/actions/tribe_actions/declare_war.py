"DeclareWar action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.tribe_actions.tribe_action import TribeAction
from tribes.types import ACTION
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class DeclareWar(TribeAction):
    def __init__(self, tribe_id: int) -> None:
        super().__init__(ACTION.DECLARE_WAR)
        self.tribe_id = tribe_id
        self._target_id: int = -1

    def set_target_id(self, target_id: int) -> None:
        self._target_id = target_id

    def get_target_id(self) -> int:
        return self._target_id

    def is_feasible(self, gs: GameState) -> bool:
        d = gs.get_board().get_diplomacy()
        allegiances = d.get_allegiance_status()
        threshold = -(float(cfg.ALLEGIANCE_MAX) / 2.0)
        return (allegiances[self.tribe_id][self._target_id] > threshold
                and not gs.get_tribe(self.tribe_id).get_has_declared_war())

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        d = gs.get_board().get_diplomacy()
        tribe = gs.get_tribe(self.tribe_id)
        tribe.set_has_declared_war(True)
        tribe.set_n_wars_declared(tribe.get_n_wars_declared() + 1)
        allegiances = d.get_allegiance_status()
        threshold = -(float(cfg.ALLEGIANCE_MAX) / 2.0)
        delta = int(threshold - allegiances[self.tribe_id][self._target_id])
        d.update_allegiance(delta, self.tribe_id, self._target_id)
        d.check_consequences(int(threshold), self.tribe_id, self._target_id)
        return True

    def copy(self) -> DeclareWar:
        dw = DeclareWar(self.tribe_id)
        dw._target_id = self._target_id
        return dw

    def __str__(self) -> str:
        return f"DECLARE_WAR by tribe {self.tribe_id} on tribe {self._target_id}"
