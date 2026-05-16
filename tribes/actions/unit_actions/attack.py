"Attack action + command."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.actions.unit_actions.unit_action import UnitAction
from tribes.types import ACTION, TURN_STATUS, TECHNOLOGY, TERRAIN, UNIT as UNIT_TYPE
from tribes.utils.vector2d import Vector2d
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState


class Attack(UnitAction):
    def __init__(self, unit_id: int) -> None:
        super().__init__(ACTION.ATTACK)
        self.unit_id = unit_id
        self._target_id: int = -1

    def set_target_id(self, target_id: int) -> None:
        self._target_id = target_id

    def get_target_id(self) -> int:
        return self._target_id

    def is_feasible(self, gs: GameState) -> bool:
        target = gs.get_actor(self._target_id)
        attacker = gs.get_actor(self.unit_id)
        if (
            target is None
            or not attacker.can_attack()
            or attacker.get_type() is UNIT_TYPE.MIND_BENDER
        ):
            return False
        return self.unit_in_range(attacker, target, gs.get_board())

    def execute(self, gs: GameState) -> bool:
        if not self.is_feasible(gs):
            return False

        d = gs.get_board().get_diplomacy()
        attacker = gs.get_actor(self.unit_id)
        target = gs.get_actor(self._target_id)

        attacker.transition_to_status(TURN_STATUS.ATTACKED)
        attacker_tribe = gs.get_tribe(attacker.tribe_id)
        attacker_tribe.reset_pacifist_count()

        attack_result, defence_result = self._get_attack_results(gs)

        d.update_allegiance(cfg.ATTACK_REPERCUSSION, attacker.tribe_id, target.tribe_id)
        d.check_consequences(
            cfg.ATTACK_REPERCUSSION, attacker.tribe_id, target.tribe_id
        )

        if target.get_current_hp() <= attack_result:
            d.update_allegiance(
                cfg.ATTACK_REPERCUSSION, attacker.tribe_id, target.tribe_id
            )
            d.check_consequences(
                cfg.ATTACK_REPERCUSSION, attacker.tribe_id, target.tribe_id
            )

            attacker.add_kill()
            attacker_tribe.add_kill()

            gs.kill_unit(target)

            melee_types = (
                UNIT_TYPE.DEFENDER,
                UNIT_TYPE.SWORDMAN,
                UNIT_TYPE.RIDER,
                UNIT_TYPE.WARRIOR,
                UNIT_TYPE.KNIGHT,
                UNIT_TYPE.SUPERUNIT,
            )
            if attacker.get_type() in melee_types:
                gs.get_board().try_push(
                    attacker_tribe,
                    attacker,
                    attacker.get_position().x,
                    attacker.get_position().y,
                    target.get_position().x,
                    target.get_position().y,
                    gs.get_random_generator(),
                )
        else:
            target.set_current_hp(target.get_current_hp() - attack_result)

            # Retaliation
            distance = Vector2d.chebychev_distance(
                attacker.get_position(), target.get_position()
            )
            if distance <= target.RANGE:
                attacker.set_current_hp(attacker.get_current_hp() - defence_result)
                if attacker.get_current_hp() <= 0:
                    target.add_kill()
                    gs.get_tribe(target.tribe_id).add_kill()
                    gs.kill_unit(attacker)

        return True

    def _get_attack_results(self, gs: GameState):
        attacker = gs.get_actor(self.unit_id)
        target = gs.get_actor(self._target_id)
        target_pos = target.get_position()
        target_tribe = gs.get_tribe(target.tribe_id)

        attack_force = attacker.ATK * (
            attacker.get_current_hp() / attacker.get_max_hp()
        )
        defence_force = target.DEF * (target.get_current_hp() / target.get_max_hp())
        accelerator = cfg.ATTACK_MODIFIER

        target_terrain = gs.get_board().get_terrain_at(target_pos.x, target_pos.y)
        if target_terrain is TERRAIN.CITY:
            city_id = gs.get_board().get_city_id_at(target_pos.x, target_pos.y)
            if target_tribe.controls_city(city_id):
                c = gs.get_actor(city_id)
                if c.has_walls():
                    defence_force *= cfg.DEFENCE_IN_WALLS
                elif target.get_type().can_fortify():
                    defence_force *= cfg.DEFENCE_BONUS
        elif (
            (
                target_terrain is TERRAIN.MOUNTAIN
                and target_tribe.get_tech_tree().is_researched(TECHNOLOGY.MEDITATION)
            )
            or (
                target_terrain is not None
                and target_terrain.is_water()
                and target_tribe.get_tech_tree().is_researched(TECHNOLOGY.AQUATISM)
            )
            or (
                target_terrain is TERRAIN.FOREST
                and target_tribe.get_tech_tree().is_researched(TECHNOLOGY.ARCHERY)
            )
        ):
            defence_force *= cfg.DEFENCE_BONUS

        total_damage = attack_force + defence_force
        attack_result = round(
            (attack_force / total_damage) * attacker.ATK * accelerator
        )
        defence_result = round(
            (defence_force / total_damage) * target.DEF * accelerator
        )
        return int(attack_result), int(defence_result)

    def copy(self) -> Attack:
        a = Attack(self.unit_id)
        a._target_id = self._target_id
        return a

    def __str__(self) -> str:
        return f"ATTACK by unit {self.unit_id} to unit {self._target_id}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Attack):
            return False
        return super().__eq__(other) and self._target_id == other._target_id
