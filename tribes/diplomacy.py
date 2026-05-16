"Diplomacy system ported from Diplomacy.java."
from __future__ import annotations

import logging

from tribes.config import ALLEGIANCE_MAX

logger = logging.getLogger(__name__)


class Diplomacy:
    """Tracks allegiance values between all tribes."""

    def __init__(self, size: int) -> None:
        self._allegiance_status: list[list[int]] = [
            [0] * size for _ in range(size)
        ]

    # ------------------------------------------------------------------

    def get_allegiance_status(self) -> list[list[int]]:
        return self._allegiance_status

    def set_allegiance_status(self, x: int, y: int, val: int) -> None:
        self._allegiance_status[x][y] = val

    def update_allegiance(self, value: int, init_tribe_id: int,
                          target_tribe_id: int) -> None:
        current = self._allegiance_status[init_tribe_id][target_tribe_id]
        if current + value < -ALLEGIANCE_MAX or current + value > ALLEGIANCE_MAX:
            value = (1 if value > 0 else -1) * (ALLEGIANCE_MAX - abs(current))
        self._allegiance_status[init_tribe_id][target_tribe_id] += value
        self._allegiance_status[target_tribe_id][init_tribe_id] += value

    def check_consequences(self, value: int, init_tribe_id: int,
                           target_tribe_id: int) -> None:
        value = value // -2
        for i in range(len(self._allegiance_status)):
            if (self._allegiance_status[i][target_tribe_id] < 0
                    and i != init_tribe_id):
                self.update_allegiance(value, i, init_tribe_id)

    def copy(self) -> Diplomacy:
        size = len(self._allegiance_status)
        d = Diplomacy(size)
        for i in range(size):
            for j in range(size):
                d.set_allegiance_status(i, j, self._allegiance_status[i][j])
        return d

    def log_allegiance(self, tribes: list) -> None:
        logger.debug("Allegiance matrix:")
        for i, row in enumerate(self._allegiance_status):
            values = ", ".join(str(v) for v in row)
            logger.debug(f"  {tribes[i].get_name()}: {values}")
