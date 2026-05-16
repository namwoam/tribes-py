"ResearchTech action + command."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tribes.actions.tribe_actions.tribe_action import TribeAction
from tribes.types import ACTION, TECHNOLOGY

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class ResearchTech(TribeAction):
    def __init__(self, tribe_id: int) -> None:
        super().__init__(ACTION.RESEARCH_TECH)
        self.tribe_id = tribe_id
        self._tech: Optional[TECHNOLOGY] = None

    def set_tech(self, tech: TECHNOLOGY) -> None:
        self._tech = tech

    def get_tech(self) -> Optional[TECHNOLOGY]:
        return self._tech

    def is_feasible(self, gs: GameState) -> bool:
        if self._tech is None:
            return False
        tribe = gs.get_tribe(self.tribe_id)
        cost = self._tech.get_cost(tribe.get_num_cities(), tribe.get_tech_tree())
        if tribe.get_stars() >= cost:
            return tribe.get_tech_tree().is_researchable(self._tech)
        return False

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False
        tech = self._tech
        tribe = gs.get_tribe(self.tribe_id)
        tech_cost = tech.get_cost(tribe.get_num_cities(), tribe.get_tech_tree())
        tribe.subtract_stars(tech_cost)
        tribe.get_tech_tree().do_research(tech)
        tribe.add_score(tech.get_points())
        if tribe.get_tech_tree().is_everything_researched():
            tribe.all_researched()
        return True

    def copy(self) -> ResearchTech:
        rt = ResearchTech(self.tribe_id)
        rt._tech = self._tech
        return rt

    def __str__(self) -> str:
        return f"RESEARCH_TECH by tribe {self.tribe_id}: {self._tech}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResearchTech):
            return False
        return super().__eq__(other) and self._tech == other._tech
