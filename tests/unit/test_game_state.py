"Unit tests for GameState."
import random
import pytest
from tribes.types import GAME_MODE, ACTION
from tribes.game.game_state import GameState


LEVEL = "levels/SampleLevel.csv"


@pytest.fixture()
def gs():
    rnd = random.Random(42)
    state = GameState(rnd, GAME_MODE.SCORE)
    state.init(LEVEL)
    return state


def test_init_loads_tribes(gs):
    tribes = gs.get_tribes()
    assert len(tribes) == 4


def test_tick_starts_at_zero(gs):
    assert gs.get_tick() == 0


def test_inc_tick(gs):
    gs.inc_tick()
    assert gs.get_tick() == 1


def test_copy_is_independent(gs):
    tribe = gs.get_tribes()[0]
    gs.init_turn(tribe)
    gs.compute_player_actions(tribe)
    copy = gs.copy()
    # Mutating copy tick should not affect original
    copy.inc_tick()
    assert gs.get_tick() != copy.get_tick()


def test_compute_player_actions_produces_end_turn(gs):
    tribe = gs.get_tribes()[0]
    gs.init_turn(tribe)
    gs.compute_player_actions(tribe)
    tribe_actions = gs.get_tribe_actions()
    types = [a.action_type for a in tribe_actions]
    assert ACTION.END_TURN in types


def test_game_not_over_at_start(gs):
    assert not gs.is_game_over()


def test_exist_available_actions_true_at_start(gs):
    tribe = gs.get_tribes()[0]
    gs.init_turn(tribe)
    gs.compute_player_actions(tribe)
    assert gs.exist_available_actions(tribe)


def test_end_turn_executes_and_sets_flag(gs):
    tribe = gs.get_tribes()[0]
    gs.init_turn(tribe)
    gs.compute_player_actions(tribe)
    from tribes.actions.tribe_actions.end_turn import EndTurn
    et = EndTurn(tribe.tribe_id)
    assert et.is_feasible(gs)
    gs.next(et)
    assert gs.is_turn_ending()


def test_board_has_correct_size(gs):
    board = gs.get_board()
    assert board.get_size() == 16  # SampleLevel.csv produces a 16×16 board
