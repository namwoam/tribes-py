"Defender unit, ported from Defender.java."

from __future__ import annotations
from tribes.actors.units.unit import Unit
from tribes.types import UNIT as UNIT_TYPE
from tribes.utils.vector2d import Vector2d
from tribes import config as cfg


class Defender(Unit):
    def __init__(
        self, pos: Vector2d, kills: int, is_veteran: bool, city_id: int, tribe_id: int
    ) -> None:
        super().__init__(
            cfg.DEFENDER_ATTACK,
            cfg.DEFENDER_DEFENCE,
            cfg.DEFENDER_MOVEMENT,
            cfg.DEFENDER_MAX_HP,
            cfg.DEFENDER_RANGE,
            cfg.DEFENDER_COST,
            pos,
            kills,
            is_veteran,
            city_id,
            tribe_id,
        )

    def get_type(self) -> UNIT_TYPE:
        return UNIT_TYPE.DEFENDER

    def copy(self, hide_info: bool = False) -> Defender:
        c = Defender(
            self.position,
            self.get_kills(),
            self.is_veteran(),
            self.get_city_id(),
            self.tribe_id,
        )
        c.set_current_hp(self.get_current_hp())
        c.set_max_hp(self.get_max_hp())
        c.set_actor_id(self.get_actor_id())
        c.set_status(self.get_status())
        return c._hide() if hide_info else c  # type: ignore[return-value]
