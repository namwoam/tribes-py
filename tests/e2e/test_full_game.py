"End-to-end tests: full game runs with different agent combinations."

from tribes.types import RESULT, TRIBE
from tribes.game.game import Game
from tribes.game.game_spec import GameSpec
from tribes.tournament import _make_agent


SEED = 42

_4P_SPEC = "levels/sample_4p.json"
_2P_SPEC = "levels/sample_2p.json"
_8P_SPEC = "levels/sample_8p.json"
_TRIBES_8 = [t.name.lower() for t in list(TRIBE)[:8]]


def _run_spec(players, spec_path=_4P_SPEC, seed=SEED):
    """Load a spec file, override players and seed, run to completion."""
    spec = GameSpec.from_file(spec_path)
    spec.players = players
    spec.seed = seed
    resolved = spec.resolve()
    agent_list = [_make_agent(p, resolved.seed) for p in resolved.players]
    game = Game()
    game.init_from_lines(
        agent_list, resolved.level_lines, resolved.seed, resolved.game_mode
    )
    game.run()
    return game


def _run_generated(players, tribes, seed=SEED, mode="score"):
    """Run a procedurally generated game."""
    spec = GameSpec(tribes=tribes, players=players, seed=seed, mode=mode)
    resolved = spec.resolve()
    agent_list = [_make_agent(p, resolved.seed) for p in resolved.players]
    game = Game()
    game.init_generated(
        agent_list,
        resolved.seed,
        resolved.tribes_enum,
        resolved.seed,
        resolved.game_mode,
    )
    game.run()
    return game


# ---------------------------------------------------------------------------
# 4-player level tests
# ---------------------------------------------------------------------------


def test_do_nothing_game_completes():
    game = _run_spec(["donothing"] * 4)
    assert len(game.get_current_ranking()) == 4


def test_do_nothing_game_has_one_winner():
    game = _run_spec(["donothing"] * 4)
    winners = [r for r in game.get_current_ranking() if r.result is RESULT.WIN]
    assert len(winners) == 1


def test_random_game_completes():
    game = _run_spec(["random"] * 4)
    assert game.get_current_ranking()


def test_mixed_agents_game_completes():
    game = _run_spec(["simple", "random", "donothing", "simple"])
    assert len(game.get_current_ranking()) == 4


def test_all_results_not_incomplete_at_game_end():
    game = _run_spec(["donothing"] * 4)
    for r in game.get_current_ranking():
        assert r.result is not RESULT.INCOMPLETE


def test_simple_agent_wins_against_do_nothing():
    """SimpleAgent should beat DoNothingAgents in the 2-player level."""
    game = _run_spec(["simple", "donothing"], spec_path=_2P_SPEC)
    ranking = game.get_current_ranking()
    winner = ranking[0]
    assert type(game.get_players()[winner.id]).__name__ == "SimpleAgent"


def test_game_scores_nonnegative():
    game = _run_spec(["random"] * 4, seed=1)
    assert all(s >= 0 for s in game.get_scores())


def test_game_2p_level_completes():
    game = _run_spec(["random", "donothing"], spec_path=_2P_SPEC)
    assert len(game.get_current_ranking()) == 2


def test_capitals_mode_game_completes():
    spec = GameSpec.from_file(_4P_SPEC)
    spec.players = ["donothing"] * 4
    spec.seed = SEED
    spec.mode = "capitals"
    resolved = spec.resolve()
    agent_list = [_make_agent(p, resolved.seed) for p in resolved.players]
    game = Game()
    game.init_from_lines(
        agent_list, resolved.level_lines, resolved.seed, resolved.game_mode
    )
    game.run()
    assert len(game.get_current_ranking()) == 4


# ---------------------------------------------------------------------------
# 8-tribe tests
# ---------------------------------------------------------------------------


def test_8_tribes_generated_completes():
    """8-tribe procedurally generated game runs to completion."""
    game = _run_generated(["random"] * 8, _TRIBES_8, seed=42)
    assert len(game.get_current_ranking()) == 8


def test_8_tribes_generated_has_one_winner():
    game = _run_generated(["random"] * 8, _TRIBES_8, seed=7)
    winners = [r for r in game.get_current_ranking() if r.result is RESULT.WIN]
    assert len(winners) == 1


def test_8_tribes_40x40_completes():
    """8-tribe game on the 40×40 hand-crafted level runs to completion."""
    game = _run_spec(["random"] * 8, spec_path=_8P_SPEC, seed=0)
    assert len(game.get_current_ranking()) == 8


def test_8_tribes_40x40_scores_nonnegative():
    game = _run_spec(["donothing"] * 8, spec_path=_8P_SPEC, seed=0)
    assert all(s >= 0 for s in game.get_scores())


# ---------------------------------------------------------------------------
# MCTS agent e2e tests
# ---------------------------------------------------------------------------


def test_mcts_2p_game_completes():
    """MCTS agent completes a 2-player game without errors."""
    game = _run_spec(["mcts", "donothing"], spec_path=_2P_SPEC, seed=SEED)
    assert len(game.get_current_ranking()) == 2


def test_mcts_2p_game_has_one_winner():
    game = _run_spec(["mcts", "donothing"], spec_path=_2P_SPEC, seed=SEED)
    winners = [r for r in game.get_current_ranking() if r.result is RESULT.WIN]
    assert len(winners) == 1


def test_mcts_all_results_not_incomplete():
    game = _run_spec(["mcts", "donothing"], spec_path=_2P_SPEC, seed=SEED)
    for r in game.get_current_ranking():
        assert r.result is not RESULT.INCOMPLETE


def test_mcts_scores_nonnegative():
    game = _run_spec(["mcts", "random"], spec_path=_2P_SPEC, seed=1)
    assert all(s >= 0 for s in game.get_scores())
