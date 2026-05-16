"Abstract Unit base class, ported from Unit.java."
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

from tribes.actors.actor import Actor
from tribes.types import TURN_STATUS, UNIT as UNIT_TYPE

if TYPE_CHECKING:
    from tribes.utils.vector2d import Vector2d

_FS = TURN_STATUS.FRESH
_MV = TURN_STATUS.MOVED
_AT = TURN_STATUS.ATTACKED
_MA = TURN_STATUS.MOVED_AND_ATTACKED
_FN = TURN_STATUS.FINISHED


class Unit(Actor):
    """Abstract base for all unit types."""

    def __init__(self, atk: int, df: int, mov: int, max_hp: int,
                 unit_range: int, cost: int,
                 pos: Vector2d, kills: int, is_veteran: bool,
                 city_id: int, tribe_id: int) -> None:
        super().__init__()
        self.ATK: int = atk
        self.DEF: int = df
        self.MOV: int = mov
        self.RANGE: int = unit_range
        self.COST: int = cost
        self._max_hp: int = max_hp
        self._current_hp: int = max_hp
        self._kills: int = kills
        self._is_veteran: bool = is_veteran
        self._city_id: int = city_id
        self.tribe_id: int = tribe_id
        self.position = pos
        self._status: TURN_STATUS = _FN

    # ------------------------------------------------------------------
    # HP
    # ------------------------------------------------------------------

    def set_current_hp(self, hp: int) -> None:
        self._current_hp = hp

    def set_max_hp(self, new_hp: int) -> None:
        self._max_hp = new_hp

    def get_max_hp(self) -> int:
        return self._max_hp

    def get_current_hp(self) -> int:
        return self._current_hp

    # ------------------------------------------------------------------
    # Kills / veteran
    # ------------------------------------------------------------------

    def set_kills(self, n_kills: int) -> None:
        self._kills = n_kills

    def get_kills(self) -> int:
        return self._kills

    def add_kill(self) -> None:
        self._kills += 1
        if self.get_type() is UNIT_TYPE.KNIGHT:
            self.set_status(_AT)

    def is_veteran(self) -> bool:
        return self._is_veteran

    def set_veteran(self, veteran: bool) -> None:
        self._is_veteran = veteran

    # ------------------------------------------------------------------
    # City
    # ------------------------------------------------------------------

    def get_city_id(self) -> int:
        return self._city_id

    def set_city_id(self, city_id: int) -> None:
        self._city_id = city_id

    # ------------------------------------------------------------------
    # Type (abstract)
    # ------------------------------------------------------------------

    @abstractmethod
    def get_type(self) -> UNIT_TYPE:
        ...

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    def get_status(self) -> TURN_STATUS:
        return self._status

    def set_status(self, status: TURN_STATUS) -> None:
        self._status = status

    def _can_transition_to(self, transition: TURN_STATUS) -> bool:
        status = self._status
        if status is _FN:
            return False
        if transition is _FN:
            return True

        utype = self.get_type()

        if utype in (UNIT_TYPE.MIND_BENDER, UNIT_TYPE.CATAPULT, UNIT_TYPE.DEFENDER):
            return (transition is _MV and status is _FS) or (transition is _AT and status is _FS)

        if utype in (UNIT_TYPE.ARCHER, UNIT_TYPE.BATTLESHIP, UNIT_TYPE.BOAT,
                     UNIT_TYPE.SHIP, UNIT_TYPE.WARRIOR, UNIT_TYPE.SWORDMAN,
                     UNIT_TYPE.SUPERUNIT):
            if transition is _MV and status is _FS:
                return True
            if transition is _AT and status is _FS:
                return True
            if transition is _AT and status is _MV:
                return True
            return False

        if utype is UNIT_TYPE.RIDER:
            if transition is _MV and status is _FS:
                return True
            if transition is _MV and status is _AT:
                return True
            if transition is _MV and status is _MA:
                return True
            if transition is _AT and status is _FS:
                return True
            if transition is _AT and status is _MV:
                return True
            return False

        if utype is UNIT_TYPE.KNIGHT:
            if transition is _MV and status is _FS:
                return True
            if transition is _AT and status is _FS:
                return True
            if transition is _AT and status is _MV:
                return True
            if transition is _AT and status is _AT:
                return True
            return False

        return False

    def transition_to_status(self, new_status: TURN_STATUS) -> None:
        if not self._can_transition_to(new_status):
            return

        if new_status is _FN:
            self._status = _FN
            return

        utype = self.get_type()

        if utype in (UNIT_TYPE.MIND_BENDER, UNIT_TYPE.CATAPULT,
                     UNIT_TYPE.DEFENDER, UNIT_TYPE.SUPERUNIT):
            self._status = _FN

        elif utype in (UNIT_TYPE.ARCHER, UNIT_TYPE.BATTLESHIP, UNIT_TYPE.BOAT,
                       UNIT_TYPE.SHIP, UNIT_TYPE.WARRIOR, UNIT_TYPE.SWORDMAN):
            s = self._status
            if new_status is _MV and s is _FS:
                self._status = _MV
            elif new_status is _AT and s is _FS:
                self._status = _FN
            elif new_status is _AT and s is _MV:
                self._status = _FN

        elif utype is UNIT_TYPE.RIDER:
            s = self._status
            if new_status is _MV and s is _FS:
                self._status = _MV
            elif new_status is _MV and s is _AT:
                self._status = _MA
            elif new_status is _MV and s is _MA:
                self._status = _FN
            elif new_status is _AT and s is _FS:
                self._status = _AT
            elif new_status is _AT and s is _MV:
                self._status = _MA

        elif utype is UNIT_TYPE.KNIGHT:
            s = self._status
            if new_status is _MV and s is _FS:
                self._status = _MV
            elif new_status is _AT and s is _FS:
                self._status = _FN
            elif new_status is _AT and s is _MV:
                self._status = _FN
            elif new_status is _AT and s is _AT:
                self._status = _FN

    def can_attack(self) -> bool:
        return self._can_transition_to(_AT)

    def can_move(self) -> bool:
        return self._can_transition_to(_MV)

    def is_finished(self) -> bool:
        return self._status is _FN

    def is_fresh(self) -> bool:
        return self._status is _FS

    # ------------------------------------------------------------------
    # Copy helper (hide sensitive info for partial obs)
    # ------------------------------------------------------------------

    def _hide(self) -> Unit:
        self._city_id = -1
        self._kills = 0
        return self

    @abstractmethod
    def copy(self, hide_info: bool) -> Unit:
        ...
