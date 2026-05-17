"Unit tests for agent implementations."

import random
import pytest
from tribes.types import ACTION, GAME_MODE
from tribes.players.do_nothing_agent import DoNothingAgent
from tribes.players.random_agent import RandomAgent
from tribes.players.simple_agent import SimpleAgent
from tribes.players.mcts import MCTSAgent, MCTSParams


@pytest.fixture()
def loaded_gs():
    """Return a GameState from the sample level, after one init_turn+compute cycle."""
    rnd = random.Random(0)
    from tribes.game.game_state import GameState
    from tribes.game.game_spec import GameSpec

    spec = GameSpec.from_file("levels/sample_4p.json")
    resolved = spec.resolve(random.Random(0))
    gs = GameState(rnd, GAME_MODE.SCORE)
    gs.init_from_lines(resolved.level_lines)
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


# ---------------------------------------------------------------------------
# MCTSAgent unit tests
# ---------------------------------------------------------------------------


def test_mcts_agent_returns_valid_action(loaded_gs):
    params = MCTSParams(TIME_BUDGET_MS=50, MAX_ITERATIONS=20)
    agent = MCTSAgent(seed=0, params=params)
    agent.set_player_ids(0, [0, 1, 2, 3])
    action = agent.act(loaded_gs)
    available = loaded_gs.get_all_available_actions()
    assert action in available


def test_mcts_agent_copy_is_independent():
    a = MCTSAgent(seed=5)
    b = a.copy()
    a.set_player_ids(0, [0, 1])
    assert b.player_id == -1


def test_mcts_agent_copy_preserves_params():
    params = MCTSParams(K=1.0, ROLLOUT_DEPTH=5)
    a = MCTSAgent(seed=3, params=params)
    b = a.copy()
    assert b._params.K == 1.0
    assert b._params.ROLLOUT_DEPTH == 5


def test_mcts_single_action_skips_search(loaded_gs):
    """When only EndTurn is available the agent must return it without searching."""
    from tribes.actions.tribe_actions.end_turn import EndTurn
    from unittest.mock import patch

    agent = MCTSAgent(seed=0)
    agent.set_player_ids(0, [0, 1, 2, 3])

    only_end_turn = [EndTurn(0)]
    with patch.object(
        loaded_gs, "get_all_available_actions", return_value=only_end_turn
    ):
        action = agent.act(loaded_gs)
    assert action.action_type is ACTION.END_TURN
