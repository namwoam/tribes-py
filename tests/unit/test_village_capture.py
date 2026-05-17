"Tests verifying that tribes can capture village tiles."

import random

import pytest

from tribes.types import ACTION, TERRAIN
from tribes.game.game_state import GameState
from tribes.game.game_spec import GameSpec
from tribes.actions.unit_actions.capture import Capture


def _gs_from_file(path, seed=42):
    spec = GameSpec.from_file(path)
    rnd = random.Random(seed)
    resolved = spec.resolve(rnd)
    gs = GameState(random.Random(seed), resolved.game_mode)
    gs.init_from_lines(resolved.level_lines)
    return gs


def _find_villages(gs):
    board = gs.get_board()
    size = board.get_size()
    return [
        (x, y)
        for x in range(size)
        for y in range(size)
        if board.get_terrain_at(x, y) is TERRAIN.VILLAGE
    ]


@pytest.fixture()
def gs_2p():
    return _gs_from_file("levels/sample_2p_villages.json")


@pytest.fixture()
def gs_4p():
    return _gs_from_file("levels/sample_4p_villages.json")


# ------------------------------------------------------------------
# board.capture() — direct API
# ------------------------------------------------------------------


class TestBoardCapture:
    def test_village_becomes_city_terrain_after_capture(self, gs_2p):
        villages = _find_villages(gs_2p)
        assert villages, "level has no villages"
        vx, vy = villages[0]
        tribe = gs_2p.get_tribes()[0]

        gs_2p.get_board().capture(gs_2p, tribe, vx, vy)

        assert gs_2p.get_board().get_terrain_at(vx, vy) is TERRAIN.CITY

    def test_capturing_tribe_gains_city(self, gs_2p):
        villages = _find_villages(gs_2p)
        vx, vy = villages[0]
        tribe = gs_2p.get_tribes()[0]
        cities_before = tribe.get_num_cities()

        gs_2p.get_board().capture(gs_2p, tribe, vx, vy)

        assert tribe.get_num_cities() == cities_before + 1

    def test_capture_awards_score(self, gs_2p):
        villages = _find_villages(gs_2p)
        vx, vy = villages[0]
        tribe = gs_2p.get_tribes()[0]
        score_before = tribe.get_score()

        gs_2p.get_board().capture(gs_2p, tribe, vx, vy)

        assert tribe.get_score() > score_before

    def test_all_villages_capturable_by_any_tribe(self, gs_4p):
        villages = _find_villages(gs_4p)
        assert villages
        tribes = gs_4p.get_tribes()
        for i, (vx, vy) in enumerate(villages):
            tribe = tribes[i % len(tribes)]
            gs_4p.get_board().capture(gs_4p, tribe, vx, vy)
            assert gs_4p.get_board().get_terrain_at(vx, vy) is TERRAIN.CITY


# ------------------------------------------------------------------
# Capture action — feasibility and execution
# ------------------------------------------------------------------


def _place_unit_at(gs, unit, x, y):
    """Teleport unit to (x, y) directly in board state for testing."""
    board = gs.get_board()
    old_pos = unit.get_position()
    board._units[old_pos.x][old_pos.y] = 0
    board._units[x][y] = unit.actor_id
    unit.position.x = x
    unit.position.y = y


class TestCaptureAction:
    def test_capture_village_is_feasible_when_unit_on_village(self, gs_2p):
        villages = _find_villages(gs_2p)
        assert villages
        vx, vy = villages[0]
        tribe = gs_2p.get_tribes()[0]

        gs_2p.init_turn(tribe)
        units = gs_2p.get_units(tribe.tribe_id)
        assert units
        unit = units[0]
        _place_unit_at(gs_2p, unit, vx, vy)

        action = Capture(unit.actor_id)
        action.set_capture_type(TERRAIN.VILLAGE)
        assert action.is_feasible(gs_2p)

    def test_capture_village_action_type(self, gs_2p):
        villages = _find_villages(gs_2p)
        vx, vy = villages[0]
        tribe = gs_2p.get_tribes()[0]

        gs_2p.init_turn(tribe)
        units = gs_2p.get_units(tribe.tribe_id)
        unit = units[0]
        _place_unit_at(gs_2p, unit, vx, vy)

        action = Capture(unit.actor_id)
        action.set_capture_type(TERRAIN.VILLAGE)
        assert action.get_action_type() is ACTION.CAPTURE

    def test_capture_village_action_executes_successfully(self, gs_2p):
        villages = _find_villages(gs_2p)
        vx, vy = villages[0]
        tribe = gs_2p.get_tribes()[0]

        gs_2p.init_turn(tribe)
        units = gs_2p.get_units(tribe.tribe_id)
        unit = units[0]
        _place_unit_at(gs_2p, unit, vx, vy)

        action = Capture(unit.actor_id)
        action.set_capture_type(TERRAIN.VILLAGE)
        result = action.execute(gs_2p)

        assert result is True
        assert gs_2p.get_board().get_terrain_at(vx, vy) is TERRAIN.CITY

    def test_capture_village_not_feasible_when_unit_elsewhere(self, gs_2p):
        villages = _find_villages(gs_2p)
        assert villages
        tribe = gs_2p.get_tribes()[0]

        gs_2p.init_turn(tribe)
        units = gs_2p.get_units(tribe.tribe_id)
        unit = units[0]

        # Unit is at capital — not on a village tile
        action = Capture(unit.actor_id)
        action.set_capture_type(TERRAIN.VILLAGE)
        assert not action.is_feasible(gs_2p)

    def test_capture_village_not_feasible_for_spent_unit(self, gs_2p):
        from tribes.types import TURN_STATUS

        villages = _find_villages(gs_2p)
        vx, vy = villages[0]
        tribe = gs_2p.get_tribes()[0]

        gs_2p.init_turn(tribe)
        units = gs_2p.get_units(tribe.tribe_id)
        unit = units[0]
        _place_unit_at(gs_2p, unit, vx, vy)
        unit.set_status(TURN_STATUS.FINISHED)

        action = Capture(unit.actor_id)
        action.set_capture_type(TERRAIN.VILLAGE)
        assert not action.is_feasible(gs_2p)
