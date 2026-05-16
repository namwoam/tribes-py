"End-to-end tests: full game runs with different agent combinations."
import pytest
from tribes.types import GAME_MODE, RESULT
from tribes.game.game import Game
from tribes.players.do_nothing_agent import DoNothingAgent
from tribes.players.random_agent import RandomAgent
from tribes.players.simple_agent import SimpleAgent


LEVEL = "levels/SampleLevel.csv"
SEED = 42


def _run_game(player_list, level=LEVEL, seed=SEED, mode=GAME_MODE.SCORE):
    game = Game()
    game.init(player_list, level, seed, mode)
    game.run()
    return game


def test_do_nothing_game_completes():
    players = [DoNothingAgent(i) for i in range(4)]
    game = _run_game(players)
    ranking = game.get_current_ranking()
    assert len(ranking) == 4


def test_do_nothing_game_has_one_winner():
    players = [DoNothingAgent(i) for i in range(4)]
    game = _run_game(players, mode=GAME_MODE.SCORE)
    ranking = game.get_current_ranking()
    winners = [r for r in ranking if r.result is RESULT.WIN]
    assert len(winners) == 1


def test_random_game_completes():
    players = [RandomAgent(i * 7) for i in range(4)]
    game = _run_game(players)
    assert game.get_current_ranking()


def test_mixed_agents_game_completes():
    players = [
        SimpleAgent(1), RandomAgent(2),
        DoNothingAgent(3), SimpleAgent(4),
    ]
    game = _run_game(players)
    ranking = game.get_current_ranking()
    assert len(ranking) == 4


def test_all_results_not_incomplete_at_game_end():
    players = [DoNothingAgent(i) for i in range(4)]
    game = _run_game(players)
    for r in game.get_current_ranking():
        assert r.result is not RESULT.INCOMPLETE


def test_simple_agent_wins_against_do_nothing(tmp_path):
    """SimpleAgent should beat DoNothingAgents in the 2-player level."""
    players = [SimpleAgent(10), DoNothingAgent(20)]
    game = Game()
    game.init(players, "levels/SampleLevel2p.csv", SEED, GAME_MODE.CAPITALS)
    game.run()
    ranking = game.get_current_ranking()
    # SimpleAgent is player 0; check its result
    winner = ranking[0]
    assert type(game.get_players()[winner.id]).__name__ == "SimpleAgent"


def test_game_scores_nonnegative():
    players = [RandomAgent(i) for i in range(4)]
    game = _run_game(players, seed=1)
    for score in game.get_scores():
        assert score >= 0


def test_game_2p_level_completes():
    players = [RandomAgent(0), DoNothingAgent(1)]
    game = Game()
    game.init(players, "levels/SampleLevel2p.csv", SEED, GAME_MODE.SCORE)
    game.run()
    assert len(game.get_current_ranking()) == 2


def test_capitals_mode_game_completes():
    players = [DoNothingAgent(i) for i in range(4)]
    game = _run_game(players, mode=GAME_MODE.CAPITALS)
    ranking = game.get_current_ranking()
    assert len(ranking) == 4
