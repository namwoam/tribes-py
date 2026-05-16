"Unit tests for agent implementations."
import random
import pytest
from tribes.types import ACTION, GAME_MODE
from tribes.players.do_nothing_agent import DoNothingAgent
from tribes.players.random_agent import RandomAgent
from tribes.players.simple_agent import SimpleAgent


@pytest.fixture()
def loaded_gs():
    """Return a GameState from the sample level, after one init_turn+compute cycle."""
    rnd = random.Random(0)
    from tribes.game.game_state import GameState
    gs = GameState(rnd, GAME_MODE.SCORE)
    gs.init("levels/sample_level.csv")
    tribe = gs.get_tribes()[0]
    gs.init_turn(tribe)
    gs.compute_player_actions(tribe)
    return gs


def test_do_nothing_always_end_turn(loaded_gs):
    agent = DoNothingAgent(seed=0)
    action = agent.act(loaded_gs)
    assert action.action_type is ACTION.END_TURN


def test_random_agent_returns_valid_action(loaded_gs):
    agent = RandomAgent(seed=42)
    action = agent.act(loaded_gs)
    available = loaded_gs.get_all_available_actions()
    assert action in available


def test_simple_agent_returns_valid_action(loaded_gs):
    agent = SimpleAgent(seed=7)
    action = agent.act(loaded_gs)
    available = loaded_gs.get_all_available_actions()
    assert action in available


def test_agent_copy_is_independent():
    a = RandomAgent(seed=10)
    b = a.copy()
    a.set_player_ids(0, [0, 1])
    # b should not be affected
    assert b.player_id == -1


def test_agent_set_player_ids():
    agent = DoNothingAgent(seed=0)
    agent.set_player_ids(2, [0, 1, 2])
    assert agent.get_player_id() == 2
    assert agent.all_player_ids == [0, 1, 2]
