"TribeResult comparable data class, ported from TribeResult.java."
from __future__ import annotations

import logging
import random

from tribes.types import RESULT

logger = logging.getLogger(__name__)


class TribeResult:
    """Holds end-of-game ranking info for one tribe.

    Ordering: WIN first, then descending score, then tie-breakers.
    """

    def __init__(self, id: int, result: RESULT, score: int,
                 num_techs_researched: int, num_cities: int,
                 production: int, num_wars: int, num_stars: int) -> None:
        self.id = id
        self.result = result
        self.score = score
        self.num_techs_researched = num_techs_researched
        self.num_cities = num_cities
        self.production = production
        self.num_wars = num_wars
        self.num_stars = num_stars

    # ------------------------------------------------------------------
    # Comparable (mirrors Java TreeSet ordering)
    # ------------------------------------------------------------------

    def _compare(self, other: TribeResult) -> int:
        """Return negative if self < other (self ranked higher)."""
        # Winning status
        if self.result == RESULT.WIN and other.result != RESULT.WIN:
            return -1
        if self.result != RESULT.WIN and other.result == RESULT.WIN:
            return 1

        # Tie breaker 0: score (higher = better)
        if self.score > other.score:
            return -1
        if self.score < other.score:
            return 1

        # Tie breaker 1: num techs researched
        if self.num_techs_researched > other.num_techs_researched:
            return -1
        if self.num_techs_researched < other.num_techs_researched:
            return 1

        # Tie breaker 2: num cities
        if self.num_cities > other.num_cities:
            return -1
        if self.num_cities < other.num_cities:
            return 1

        # Tie breaker 3: production
        if self.production > other.production:
            return -1
        if self.production < other.production:
            return 1

        # Tie breaker 4: wars
        if self.num_wars > other.num_wars:
            return -1
        if self.num_wars < other.num_wars:
            return 1

        # Tie breaker 5: stars
        if self.num_stars > other.num_stars:
            return -1
        if self.num_stars < other.num_stars:
            return 1

        # random tie-break (mirrors Java)
        return -1 if random.random() < 0.5 else 1

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, TribeResult):
            return NotImplemented
        return self._compare(other) < 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TribeResult):
            return NotImplemented
        return self._compare(other) == 0

    def __le__(self, other: object) -> bool:
        return self.__lt__(other) or self.__eq__(other)

    # ------------------------------------------------------------------
    # Accessors / mutators
    # ------------------------------------------------------------------

    def get_id(self) -> int:
        return self.id

    def get_result(self) -> RESULT:
        return self.result

    def set_result(self, result: RESULT) -> None:
        self.result = result

    def get_score(self) -> int:
        return self.score

    def get_num_techs_researched(self) -> int:
        return self.num_techs_researched

    def get_num_cities(self) -> int:
        return self.num_cities

    def get_production(self) -> int:
        return self.production

    def get_num_wars(self) -> int:
        return self.num_wars

    def get_num_stars(self) -> int:
        return self.num_stars

    def copy(self) -> TribeResult:
        return TribeResult(
            self.id, self.result, self.score, self.num_techs_researched,
            self.num_cities, self.production, self.num_wars, self.num_stars
        )
