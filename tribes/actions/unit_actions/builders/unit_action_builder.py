"UnitActionBuilder, ported from UnitActionBuilder.java."
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game_state import GameState
    from tribes.actors.units.unit import Unit
    from tribes.actions.action import Action


class UnitActionBuilder:
    def get_actions(self, gs: GameState, unit: Unit) -> list[Action]:
        from tribes.actions.unit_actions.builders.upgrade_factory import UpgradeFactory
        from tribes.actions.unit_actions.builders.attack_factory import AttackFactory
        from tribes.actions.unit_actions.builders.capture_factory import CaptureFactory
        from tribes.actions.unit_actions.builders.convert_factory import ConvertFactory
        from tribes.actions.unit_actions.builders.disband_factory import DisbandFactory
        from tribes.actions.unit_actions.builders.examine_factory import ExamineFactory
        from tribes.actions.unit_actions.builders.heal_others_factory import HealOthersFactory
        from tribes.actions.unit_actions.builders.make_veteran_factory import MakeVeteranFactory
        from tribes.actions.unit_actions.builders.move_factory import MoveFactory
        from tribes.actions.unit_actions.builders.recover_factory import RecoverFactory

        all_actions: list[Action] = []

        if unit.tribe_id != gs.get_active_tribe_id():
            logger.error(
                f"Creating actions for unit {unit.actor_id} not controlled by active tribe "
                f"{gs.get_active_tribe_id()} (unit tribe {unit.tribe_id})")
            return all_actions

        # Upgrade always possible
        all_actions.extend(UpgradeFactory().compute_action_variants(unit, gs))

        if unit.is_finished():
            return all_actions

        all_actions.extend(AttackFactory().compute_action_variants(unit, gs))
        all_actions.extend(CaptureFactory().compute_action_variants(unit, gs))
        all_actions.extend(ConvertFactory().compute_action_variants(unit, gs))
        all_actions.extend(DisbandFactory().compute_action_variants(unit, gs))
        all_actions.extend(ExamineFactory().compute_action_variants(unit, gs))
        all_actions.extend(HealOthersFactory().compute_action_variants(unit, gs))
        all_actions.extend(MakeVeteranFactory().compute_action_variants(unit, gs))
        all_actions.extend(MoveFactory().compute_action_variants(unit, gs))
        all_actions.extend(RecoverFactory().compute_action_variants(unit, gs))

        return all_actions
