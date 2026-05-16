"SendStars action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.tribe_actions.tribe_action import TribeAction
from tribes.types import ACTION
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class SendStars(TribeAction):
    def __init__(self, tribe_id: int) -> None:
        super().__init__(ACTION.SEND_STARS)
        self.tribe_id = tribe_id
        self._num_stars: int = 0
        self._target_id: int = -1

    def set_num_stars(self, num_stars: int) -> None:
        self._num_stars = num_stars

    def get_num_stars(self) -> int:
        return self._num_stars

    def set_target_id(self, target_id: int) -> None:
        self._target_id = target_id

    def get_target_id(self) -> int:
        return self._target_id

    def is_feasible(self, gs: GameState) -> bool:
        tribe = gs.get_tribe(self.tribe_id)
        return tribe.can_send_stars(self._num_stars) and self._num_stars <= cfg.MIN_STARS_SEND

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        tribe = gs.get_tribe(self.tribe_id)
        target = gs.get_tribe(self._target_id)
        tribe.subtract_stars(self._num_stars)
        target.add_stars(self._num_stars)
        tribe.set_stars_sent(tribe.get_stars_sent() + self._num_stars)
        tribe.set_n_stars_sent(tribe.get_n_stars_sent() + self._num_stars)
        tribe.add_score(self._num_stars)
        d = gs.get_board().get_diplomacy()
        d.update_allegiance(self._num_stars, self.tribe_id, self._target_id)
        d.check_consequences(self._num_stars, self.tribe_id, self._target_id)
        return True

    def copy(self) -> SendStars:
        ss = SendStars(self.tribe_id)
        ss._num_stars = self._num_stars
        ss._target_id = self._target_id
        return ss

    def __str__(self) -> str:
        return f"SEND_STARS by tribe {self.tribe_id} to: {self._target_id}: {self._num_stars} stars"
