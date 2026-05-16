"Ship unit, ported from Ship.java."

from __future__ import annotations
from typing import Optional
from tribes.actors.units.unit import Unit
from tribes.types import UNIT as UNIT_TYPE
from tribes.utils.vector2d import Vector2d
from tribes import config as cfg


class Ship(Unit):
    def __init__(
        self, pos: Vector2d, kills: int, is_veteran: bool, city_id: int, tribe_id: int
    ) -> None:
        super().__init__(
            cfg.SHIP_ATTACK,
            cfg.SHIP_DEFENCE,
            cfg.SHIP_MOVEMENT,
            -1,
            cfg.SHIP_RANGE,
            cfg.SHIP_COST,
            pos,
            kills,
            is_veteran,
            city_id,
            tribe_id,
        )
        self._base_land_unit: Optional[UNIT_TYPE] = None

    def get_base_land_unit(self) -> Optional[UNIT_TYPE]:
        return self._base_land_unit

    def set_base_land_unit(self, unit_type: Optional[UNIT_TYPE]) -> None:
        self._base_land_unit = unit_type

    def get_type(self) -> UNIT_TYPE:
        return UNIT_TYPE.SHIP

    def copy(self, hide_info: bool = False) -> Ship:
        c = Ship(
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
        c.set_base_land_unit(self.get_base_land_unit())
        return c._hide() if hide_info else c  # type: ignore[return-value]
