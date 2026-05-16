"SimpleAgent: heuristic-scored action selection, ported from SimpleAgent.java."
from __future__ import annotations

import logging
import random
from collections import defaultdict
from typing import TYPE_CHECKING

from tribes.players.agent import Agent
from tribes.types import ACTION, TECHNOLOGY, TERRAIN, BUILDING as BUILDING_TYPE, UNIT as UNIT_TYPE, CITY_LEVEL_UP

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.actions.action import Action
    from tribes.game.game_state import GameState
    from tribes.actors.tribe import Tribe
    from tribes.actors.city import City
    from tribes.actors.units.unit import Unit


class SimpleAgent(Agent):
    """Rule-based agent that scores every action and picks the best."""

    def __init__(self, seed: int) -> None:
        super().__init__(seed)
        self._rnd = random.Random(seed)

    def copy(self) -> SimpleAgent:
        return SimpleAgent(self.seed)

    def act(self, gs: GameState) -> Action:
        all_actions = gs.get_all_available_actions()
        best_score = -999
        buckets: dict[int, list[Action]] = defaultdict(list)

        for a in all_actions:
            score = self._eval_action(gs, a)
            buckets[score].append(a)
            if score > best_score:
                best_score = score

        # Walk down from best score until we find a non-empty bucket
        val = best_score
        while val >= -2:
            if buckets[val]:
                return self._rnd.choice(buckets[val])
            val -= 1

        return self._rnd.choice(all_actions)

    # ------------------------------------------------------------------
    # Action scoring
    # ------------------------------------------------------------------

    def _eval_action(self, gs: GameState, a: Action) -> int:
        tribe = gs.get_active_tribe()
        at = a.action_type

        # Unit actions
        if at is ACTION.MOVE:
            return self._eval_move(a, gs, tribe)
        if at is ACTION.ATTACK:
            return self._eval_attack(a, gs)
        if at in (ACTION.UPGRADE_BOAT, ACTION.UPGRADE_SHIP):
            return self._eval_upgrade(a, gs, tribe)
        if at is ACTION.RECOVER:
            return self._eval_recover(a, gs, tribe)
        if at in (ACTION.CAPTURE, ACTION.EXAMINE):
            return 5
        if at is ACTION.HEAL_OTHERS:
            return self._eval_heal(a, gs)
        if at is ACTION.CONVERT:
            return self._eval_convert(a, gs)
        if at is ACTION.MAKE_VETERAN:
            return 5
        if at is ACTION.DISBAND:
            return -2

        # City actions
        if at is ACTION.DESTROY:
            return -2
        if at is ACTION.BURN_FOREST:
            return self._eval_burn(a, gs, tribe)
        if at is ACTION.CLEAR_FOREST:
            return self._eval_clear(tribe)
        if at is ACTION.GROW_FOREST:
            return self._eval_grow(a, gs)
        if at is ACTION.BUILD:
            return self._eval_build(a, gs, tribe)
        if at is ACTION.SPAWN:
            return self._eval_spawn(a, gs, tribe)
        if at is ACTION.RESOURCE_GATHERING:
            return self._eval_resource_gathering(a, gs)
        if at is ACTION.LEVEL_UP:
            return self._eval_level_up(a)

        # Tribe actions
        if at is ACTION.BUILD_ROAD:
            return self._eval_road(a, gs, tribe)
        if at is ACTION.RESEARCH_TECH:
            return self._eval_research(a, gs, tribe)
        if at is ACTION.SEND_STARS:
            return self._eval_send_stars(a, gs, tribe)
        if at is ACTION.END_TURN:
            return -1

        return 0

    # ------------------------------------------------------------------
    # Individual evaluators
    # ------------------------------------------------------------------

    def _eval_send_stars(self, a: Action, gs: GameState, tribe: Tribe) -> int:
        ss = a
        num_stars = tribe.get_stars()
        d = gs.get_board().get_diplomacy()
        allegiance = d.get_allegiance_status()[tribe.tribe_id][ss.get_target_id()]

        if num_stars > 60:
            return 4
        if num_stars > 30:
            if allegiance < 0 and allegiance + ss.get_num_stars() > 0:
                return 3
            return 2
        if -5 <= allegiance < 0 and ss.get_num_stars() <= 5:
            return 4
        return -1

    def _eval_level_up(self, a: Action) -> int:
        good = {CITY_LEVEL_UP.BORDER_GROWTH, CITY_LEVEL_UP.WORKSHOP,
                CITY_LEVEL_UP.RESOURCES, CITY_LEVEL_UP.SUPERUNIT}
        if a.get_bonus() in good:
            return 5
        return 0

    def _eval_resource_gathering(self, a: Action, gs: GameState) -> int:
        city: City = gs.get_actor(a.get_city_id())
        needed = self._needed_to_level_up(city)
        return min(5, max(0, 5 - needed))

    def _needed_to_level_up(self, city: City) -> int:
        return city.get_level() + 1 - city.get_production()

    def _eval_road(self, a: Action, gs: GameState, tribe: Tribe) -> int:
        from tribes.utils.vector2d import Vector2d
        pos = a.get_position()
        board = gs.get_board()
        for neigh in pos.neighborhood(1, 0, board.get_size()):
            x, y = neigh.x, neigh.y
            city = board.get_city_in_borders(x, y)
            if city is not None and city.get_tribe_id() == tribe.tribe_id:
                if x == city.get_position().x and y == city.get_position().y:
                    if tribe.get_max_production(gs) > 5 and tribe.get_stars() > 4:
                        return 3
                else:
                    if board.is_road(x, y):
                        return 3
            elif board.is_road(x, y):
                if tribe.get_max_production(gs) > 5 and tribe.get_stars() > 4:
                    return 4
                return 3
        return 0

    def _eval_spawn(self, a: Action, gs: GameState, tribe: Tribe) -> int:
        u_type: UNIT_TYPE = a.get_unit_type()
        city_id: int = a.get_city_id()
        obs_grid = tribe.get_obs_grid()
        enemies_in_city = 0
        for pos in gs.get_board().get_city_tiles(city_id):
            if obs_grid[pos.x][pos.y]:
                unit = gs.get_board().get_unit_at(pos.x, pos.y)
                if unit is not None and unit.get_tribe_id() != tribe.tribe_id:
                    enemies_in_city += 1

        if u_type in (UNIT_TYPE.RIDER, UNIT_TYPE.ARCHER, UNIT_TYPE.CATAPULT):
            return 0 if enemies_in_city > 0 else 3
        if u_type in (UNIT_TYPE.SWORDMAN, UNIT_TYPE.KNIGHT):
            return 4 if enemies_in_city > 0 else 3
        if u_type is UNIT_TYPE.MIND_BENDER:
            return 0 if enemies_in_city > 0 else 2
        if u_type is UNIT_TYPE.WARRIOR:
            return 3
        if u_type is UNIT_TYPE.DEFENDER:
            return 5 if enemies_in_city > 0 else 3
        return 0

    def _eval_research(self, a: Action, gs: GameState, tribe: Tribe) -> int:
        tech: TECHNOLOGY = a.get_tech()
        tier1_prio = {TECHNOLOGY.ORGANIZATION, TECHNOLOGY.CLIMBING, TECHNOLOGY.MINING,
                      TECHNOLOGY.FISHING, TECHNOLOGY.HUNTING, TECHNOLOGY.WHALING}
        tier2_prio = {TECHNOLOGY.FARMING, TECHNOLOGY.AQUATISM, TECHNOLOGY.RIDING,
                      TECHNOLOGY.FORESTRY, TECHNOLOGY.ARCHERY, TECHNOLOGY.SAILING,
                      TECHNOLOGY.SHIELDS, TECHNOLOGY.CHIVALRY}
        if tech in tier1_prio:
            return 5
        if tech in tier2_prio:
            return 4
        return 3

    def _eval_grow(self, a: Action, gs: GameState) -> int:
        city_id = a.get_city_id()
        city_tiles = gs.get_board().get_city_tiles(city_id)
        n_forests = 0
        n_lumber = 0
        for pos in city_tiles:
            if gs.get_board().get_terrain_at(pos.x, pos.y) is TERRAIN.FOREST:
                n_forests += 1
            b = gs.get_board().get_building_at(pos.x, pos.y)
            if b is BUILDING_TYPE.LUMBER_HUT:
                n_lumber += 1
        if n_forests < 2 and n_lumber < 2:
            return 4
        return 2

    def _eval_clear(self, tribe: Tribe) -> int:
        return 3 if tribe.get_stars() == 0 else 0

    def _eval_burn(self, a: Action, gs: GameState, tribe: Tribe) -> int:
        city: City = gs.get_actor(a.get_city_id())
        if city is None or tribe.get_stars() <= 5:
            return 0
        score = 1
        n_farms = sum(1 for b in city.get_buildings()
                      if b.type is BUILDING_TYPE.FARM)
        if n_farms < 2:
            score += n_farms
        return min(5, score)

    def _eval_build(self, a: Action, gs: GameState, tribe: Tribe) -> int:
        if tribe.get_stars() < 8:
            return 0
        b_type: BUILDING_TYPE = a.get_building_type()
        monuments = {BUILDING_TYPE.GRAND_BAZAR, BUILDING_TYPE.EMPERORS_TOMB,
                     BUILDING_TYPE.GATE_OF_POWER, BUILDING_TYPE.EYE_OF_GOD,
                     BUILDING_TYPE.PARK_OF_FORTUNE, BUILDING_TYPE.TOWER_OF_WISDOM,
                     BUILDING_TYPE.ALTAR_OF_PEACE}
        temples = {BUILDING_TYPE.TEMPLE, BUILDING_TYPE.WATER_TEMPLE, BUILDING_TYPE.MOUNTAIN_TEMPLE}
        mid_tier = {BUILDING_TYPE.FARM, BUILDING_TYPE.MINE, BUILDING_TYPE.FORGE,
                    BUILDING_TYPE.WINDMILL, BUILDING_TYPE.CUSTOMS_HOUSE}
        low_tier = {BUILDING_TYPE.PORT, BUILDING_TYPE.SAWMILL, BUILDING_TYPE.LUMBER_HUT}

        if b_type in monuments:
            score = 5
        elif b_type in mid_tier:
            score = 4
        elif b_type in low_tier:
            score = 3
        elif b_type in temples:
            score = 1
        else:
            score = 0

        city: City = gs.get_actor(a.get_city_id())
        needed = self._needed_to_level_up(city)
        return min(5, max(0, score + 5 - needed))

    def _eval_upgrade(self, a: Action, gs: GameState, tribe: Tribe) -> int:
        unit: Unit = gs.get_actor(a.get_unit_id())
        if unit.get_type() is UNIT_TYPE.BATTLESHIP:
            if tribe.get_max_production(gs) > 5 and tribe.get_stars() > 8:
                return 3
        else:
            if tribe.get_max_production(gs) > 3 and tribe.get_stars() > 6:
                return 3
        return 0

    def _eval_recover(self, a: Action, gs: GameState, tribe: Tribe) -> int:
        obs_grid = tribe.get_obs_grid()
        this_unit: Unit = gs.get_actor(a.get_unit_id())
        board = gs.get_board()
        for x in range(len(obs_grid)):
            for y in range(len(obs_grid[x])):
                if obs_grid[x][y]:
                    enemy = board.get_unit_at(x, y)
                    if enemy is not None and enemy.get_tribe_id() != tribe.tribe_id:
                        if self._check_in_range(enemy, this_unit):
                            if enemy.get_current_hp() < this_unit.get_current_hp():
                                return 3
                            return 1
        return 4

    def _eval_heal(self, a: Action, gs: GameState) -> int:
        this_unit: Unit = gs.get_actor(a.get_unit_id())
        board = gs.get_board()
        potential_heals = 0
        targets = a.get_targets(gs)
        for target in targets:
            if target.get_current_hp() < target.get_max_hp():
                for t in this_unit.get_position().neighborhood(target.RANGE, 0, board.get_size()):
                    enemy = board.get_unit_at(t.x, t.y)
                    if (enemy is not None
                            and enemy.get_tribe_id() != target.get_tribe_id()
                            and enemy.get_current_hp() > target.get_current_hp()):
                        potential_heals += 1
        return min(potential_heals, 5)

    def _eval_convert(self, a: Action, gs: GameState) -> int:
        defender: Unit = gs.get_actor(a.get_target_id())
        attacker: Unit = gs.get_actor(a.unit_id)
        if defender is None or attacker is None:
            return 0
        d = gs.get_board().get_diplomacy()
        allegiance = d.get_allegiance_status()[attacker.get_tribe_id()][defender.get_tribe_id()]
        high_value = {UNIT_TYPE.BATTLESHIP, UNIT_TYPE.SUPERUNIT, UNIT_TYPE.SWORDMAN,
                      UNIT_TYPE.KNIGHT, UNIT_TYPE.CATAPULT}
        mid_value = {UNIT_TYPE.MIND_BENDER, UNIT_TYPE.BOAT, UNIT_TYPE.SHIP, UNIT_TYPE.WARRIOR}
        if defender.get_type() in high_value:
            if allegiance < 0:
                return 5
            if allegiance < 15:
                return 2
        if defender.get_type() in mid_value:
            if allegiance < 0:
                return 4
            if allegiance < 15:
                return 1
        return 0

    def _eval_move(self, a: Action, gs: GameState, tribe: Tribe) -> int:
        from tribes.utils.vector2d import Vector2d
        dest = a.get_destination()
        this_unit: Unit = gs.get_actor(a.get_unit_id())
        current_pos = this_unit.get_position()
        board = gs.get_board()
        obs_grid = tribe.get_obs_grid()

        max_cities = 3
        for tid in tribe.get_tribes_met():
            other = gs.get_tribe(tid)
            if other.get_num_cities() > max_cities:
                max_cities = other.get_num_cities()

        # Check enemy proximity
        for x in range(len(obs_grid)):
            for y in range(len(obs_grid[x])):
                if obs_grid[x][y]:
                    enemy = board.get_unit_at(x, y)
                    if enemy is not None and enemy.get_tribe_id() != tribe.tribe_id:
                        in_range = self._check_in_range(enemy, this_unit)
                        if (enemy.DEF < this_unit.ATK
                                and this_unit.get_current_hp() >= enemy.get_current_hp()):
                            if (Vector2d.chebychev_distance(dest, enemy.get_position()) <
                                    Vector2d.chebychev_distance(current_pos, enemy.get_position())):
                                return 3
                        else:
                            if (Vector2d.chebychev_distance(dest, enemy.get_position()) >
                                    Vector2d.chebychev_distance(current_pos, enemy.get_position())
                                    and in_range):
                                return 4

        # Check nearby cities and villages
        for neigh in this_unit.get_position().neighborhood(this_unit.RANGE, 0, board.get_size()):
            x, y = neigh.x, neigh.y
            if obs_grid[x][y]:
                city = board.get_city_in_borders(x, y)
                terrain = board.get_terrain_at(x, y)
                if city is not None and city.get_tribe_id() != tribe.tribe_id:
                    if (Vector2d.chebychev_distance(dest, city.get_position()) <
                            Vector2d.chebychev_distance(this_unit.get_position(), city.get_position())):
                        return 4
                if terrain is TERRAIN.VILLAGE:
                    from tribes.utils.vector2d import Vector2d as V
                    village_pos = V(x, y)
                    if (Vector2d.chebychev_distance(dest, village_pos) <
                            Vector2d.chebychev_distance(this_unit.get_position(), village_pos)):
                        return 5

        # Encourage exploration: move next to fog
        for neigh in dest.neighborhood(1, 0, board.get_size()):
            if obs_grid[neigh.x][neigh.y]:
                return 3

        return 0

    def _eval_attack(self, a: Action, gs: GameState) -> int:
        attacker: Unit = gs.get_actor(a.get_unit_id())
        defender: Unit = gs.get_actor(a.get_target_id())
        board = gs.get_board()
        d = board.get_diplomacy()
        allegiance = d.get_allegiance_status()[attacker.get_tribe_id()][defender.get_tribe_id()]

        if not attacker.get_type().is_ranged():
            if attacker.get_current_hp() >= defender.get_current_hp():
                if attacker.ATK > defender.DEF:
                    if allegiance < 0:
                        return 5
                    return 2 if allegiance < 15 else 0
                return 1 if allegiance < 0 else 0
            else:
                if attacker.ATK > defender.DEF:
                    return 1 if allegiance < 0 else 0
        else:
            in_enemy_range = self._check_in_range(defender, attacker)
            enemy_in_range = self._check_in_range(attacker, defender)
            if in_enemy_range and defender.ATK > attacker.DEF:
                return 0
            if enemy_in_range and not in_enemy_range:
                if allegiance < 0:
                    return 5
                return 2 if allegiance < 15 else 0
            if defender.DEF < attacker.ATK and attacker.get_current_hp() >= defender.get_current_hp():
                if allegiance < 0:
                    return 4
                return 1 if allegiance < 15 else 0
        return 0

    def _check_in_range(self, attacker: Unit, defender: Unit) -> bool:
        from tribes.utils.vector2d import Vector2d
        return (Vector2d.chebychev_distance(defender.get_position(), attacker.get_position())
                <= attacker.RANGE)
