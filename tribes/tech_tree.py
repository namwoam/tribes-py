"Technology tree ported from TechnologyTree.java."
from __future__ import annotations

import random as _random
from typing import Optional

from tribes.types import TECHNOLOGY

_TECH_LIST = list(TECHNOLOGY)
_TECH_ORDINAL: dict[TECHNOLOGY, int] = {t: i for i, t in enumerate(_TECH_LIST)}


class TechnologyTree:
    """Tracks which technologies have been researched."""

    def __init__(self, researched: Optional[list[bool]] = None) -> None:
        num = len(_TECH_LIST)
        if researched is None:
            self.researched: list[bool] = [False] * num
        else:
            self.researched = list(researched)
        self._everything_researched: bool = False
        if researched is not None:
            self._check_everything_researched()

    # ------------------------------------------------------------------

    def is_researched(self, target: Optional[TECHNOLOGY]) -> bool:
        if target is None:
            return False
        return self.researched[_TECH_ORDINAL[target]]

    def is_researchable(self, target: TECHNOLOGY) -> bool:
        requirement = target.get_parent_tech()
        return not self.is_researched(target) and (
            requirement is None or self.is_researched(requirement)
        )

    def _check_everything_researched(self) -> None:
        for b in self.researched:
            if not b:
                return
        self._everything_researched = True

    def is_everything_researched(self) -> bool:
        return self._everything_researched

    def do_research(self, target: TECHNOLOGY) -> bool:
        if self.is_researchable(target):
            self.researched[_TECH_ORDINAL[target]] = True
            leaf_techs = {
                TECHNOLOGY.SHIELDS, TECHNOLOGY.AQUATISM, TECHNOLOGY.CHIVALRY,
                TECHNOLOGY.CONSTRUCTION, TECHNOLOGY.MATHEMATICS, TECHNOLOGY.NAVIGATION,
                TECHNOLOGY.SMITHERY, TECHNOLOGY.SPIRITUALISM, TECHNOLOGY.TRADE,
                TECHNOLOGY.PHILOSOPHY,
            }
            if target in leaf_techs:
                self._check_everything_researched()
            return True
        return False

    def do_research_init(self, target: TECHNOLOGY) -> None:
        """Research initial technology, bypassing parent requirements."""
        self.researched[_TECH_ORDINAL[target]] = True

    def copy(self) -> TechnologyTree:
        return TechnologyTree(self.researched)

    def get_num_researched(self) -> int:
        return sum(1 for t in TECHNOLOGY if self.is_researched(t))

    def research_at_random(self, rnd: _random.Random) -> bool:
        if self.is_everything_researched():
            return False
        available = [t for t in TECHNOLOGY if self.is_researchable(t)]
        if not available:
            return False
        t = available[rnd.randint(0, len(available) - 1)]
        return self.do_research(t)

    def get_researched(self) -> list[bool]:
        return self.researched
