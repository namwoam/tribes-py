"CityActionBuilder, ported from CityActionBuilder.java."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState
    from tribes.actors.city import City
    from tribes.actions.action import Action


class CityActionBuilder:
    def __init__(self) -> None:
        self._level_up_flag: bool = False

    def get_actions(self, gs: GameState, city: City) -> list[Action]:
        from tribes.actions.city_actions.builders.level_up_factory import LevelUpFactory
        from tribes.actions.city_actions.builders.build_factory import BuildFactory
        from tribes.actions.city_actions.builders.burn_forest_factory import BurnForestFactory
        from tribes.actions.city_actions.builders.clear_forest_factory import ClearForestFactory
        from tribes.actions.city_actions.builders.destroy_factory import DestroyFactory
        from tribes.actions.city_actions.builders.grow_forest_factory import GrowForestFactory
        from tribes.actions.city_actions.builders.resource_gathering_factory import ResourceGatheringFactory
        from tribes.actions.city_actions.builders.spawn_factory import SpawnFactory

        all_actions: list[Action] = []
        self._level_up_flag = False

        if city.tribe_id != gs.get_active_tribe_id():
            logger.error(f"Creating actions for city {city.actor_id} not controlled by active tribe.")
            return all_actions

        # Level Up is checked first
        all_actions.extend(LevelUpFactory().compute_action_variants(city, gs))
        if len(all_actions) > 0:
            self._level_up_flag = True
            return all_actions

        all_actions.extend(BuildFactory().compute_action_variants(city, gs))
        all_actions.extend(BurnForestFactory().compute_action_variants(city, gs))
        all_actions.extend(ClearForestFactory().compute_action_variants(city, gs))
        all_actions.extend(DestroyFactory().compute_action_variants(city, gs))
        all_actions.extend(GrowForestFactory().compute_action_variants(city, gs))
        all_actions.extend(ResourceGatheringFactory().compute_action_variants(city, gs))
        all_actions.extend(SpawnFactory().compute_action_variants(city, gs))

        return all_actions

    def city_levels_up(self) -> bool:
        return self._level_up_flag
