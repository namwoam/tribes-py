"TribeActionBuilder, ported from TribeActionBuilder.java."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState
    from tribes.actors.tribe import Tribe
    from tribes.actions.action import Action


class TribeActionBuilder:
    def get_actions(self, gs: GameState, tribe: Tribe) -> list[Action]:
        from tribes.actions.tribe_actions.build_road import BuildRoad
        from tribes.actions.tribe_actions.research_tech import ResearchTech
        from tribes.actions.tribe_actions.declare_war import DeclareWar
        from tribes.actions.tribe_actions.send_stars import SendStars
        from tribes.actions.tribe_actions.end_turn import EndTurn
        from tribes.types import TECHNOLOGY
        from tribes import config as cfg

        all_actions: list[Action] = []

        if tribe.tribe_id != gs.get_active_tribe_id():
            logger.error(
                f"Creating actions for tribe {tribe.tribe_id} that is not active."
            )
            return all_actions

        # Build Road
        if tribe.can_build_roads():
            positions = gs.get_board().get_build_road_positions(tribe.tribe_id)
            for v in positions:
                br = BuildRoad(tribe.tribe_id)
                br.set_position(v)
                all_actions.append(br)

        # Research Tech
        tech_tree = tribe.get_tech_tree()
        stars = tribe.get_stars()
        num_cities = tribe.get_num_cities()
        for tech in TECHNOLOGY:
            if stars >= tech.get_cost(
                num_cities, tech_tree
            ) and tech_tree.is_researchable(tech):
                rt = ResearchTech(tribe.tribe_id)
                rt.set_tech(tech)
                all_actions.append(rt)

        # Declare War
        d = gs.get_board().get_diplomacy()
        allegiances = d.get_allegiance_status()
        threshold = -(float(cfg.ALLEGIANCE_MAX) / 2.0)
        if not tribe.get_has_declared_war():
            for i in range(len(allegiances)):
                if allegiances[tribe.tribe_id][i] > threshold and tribe.tribe_id != i:
                    dw = DeclareWar(tribe.tribe_id)
                    dw.set_target_id(i)
                    all_actions.append(dw)

        # Send Stars
        if tribe.get_stars() > 0:
            tribes = gs.get_board().get_tribes()
            for ids in range(len(tribes)):
                for stars_to_send in range(
                    1, min(tribe.get_stars(), cfg.MIN_STARS_SEND)
                ):
                    if ids != tribe.tribe_id and tribe.can_send_stars(stars_to_send):
                        ss = SendStars(tribe.tribe_id)
                        ss.set_num_stars(stars_to_send)
                        ss.set_target_id(ids)
                        all_actions.append(ss)

        # End Turn
        if gs.can_end_turn(tribe.tribe_id):
            all_actions.append(EndTurn(tribe.actor_id))

        return all_actions
