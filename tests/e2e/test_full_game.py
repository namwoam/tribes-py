"End-to-end tests: full game runs with different agent combinations."

from tribes.types import RESULT, TRIBE
from tribes.game.game import Game
from tribes.game.game_spec import GameSpec
from tribes.tournament import _make_agent


SEED = 42

_4P_LEVEL = "levels/sample_level.csv"
_2P_LEVEL = "levels/sample_level_2p.csv"
_8P_LEVEL = "levels/sample_level_8p_40x40.csv"
_TRIBES_8 = [t.name.lower() for t in list(TRIBE)[:8]]


def _make_players(types, seed=SEED):
    return [_make_agent(t, seed) for t in types]


def _run_spec(spec_dict, seed=SEED):
    """Run a game from a spec dict and return the completed Game."""
    spec = GameSpec.from_dict({**spec_dict, "seed": seed})
    resolved = spec.resolve()
    players = _make_players(resolved.players, resolved.seed)
    game = Game()
    if resolved.level_lines is not None:
        game.init_from_lines(
            players, resolved.level_lines, resolved.seed, resolved.game_mode
        )
    else:
        game.init_generated(
            players,
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
    game = _run_spec(
        {"level": _4P_LEVEL, "players": ["donothing"] * 4, "mode": "score"}
    )
    assert len(game.get_current_ranking()) == 4


def test_do_nothing_game_has_one_winner():
    game = _run_spec(
        {"level": _4P_LEVEL, "players": ["donothing"] * 4, "mode": "score"}
    )
    winners = [r for r in game.get_current_ranking() if r.result is RESULT.WIN]
    assert len(winners) == 1


def test_random_game_completes():
    game = _run_spec({"level": _4P_LEVEL, "players": ["random"] * 4, "mode": "score"})
    assert game.get_current_ranking()


def test_mixed_agents_game_completes():
    game = _run_spec(
        {
            "level": _4P_LEVEL,
            "players": ["simple", "random", "donothing", "simple"],
            "mode": "score",
        }
    )
    assert len(game.get_current_ranking()) == 4


def test_all_results_not_incomplete_at_game_end():
    game = _run_spec(
        {"level": _4P_LEVEL, "players": ["donothing"] * 4, "mode": "score"}
    )
    for r in game.get_current_ranking():
        assert r.result is not RESULT.INCOMPLETE


def test_simple_agent_wins_against_do_nothing():
    """SimpleAgent should beat DoNothingAgents in the 2-player level."""
    spec = GameSpec.from_dict(
        {
            "level": _2P_LEVEL,
            "players": ["simple", "donothing"],
            "mode": "capitals",
            "seed": SEED,
        }
    )
    resolved = spec.resolve()
    players = _make_players(resolved.players, resolved.seed)
    game = Game()
    game.init_from_lines(
        players, resolved.level_lines, resolved.seed, resolved.game_mode
    )
    game.run()
    ranking = game.get_current_ranking()
    winner = ranking[0]
    assert type(game.get_players()[winner.id]).__name__ == "SimpleAgent"


def test_game_scores_nonnegative():
    game = _run_spec(
        {"level": _4P_LEVEL, "players": ["random"] * 4, "mode": "score"}, seed=1
    )
    assert all(s >= 0 for s in game.get_scores())


def test_game_2p_level_completes():
    game = _run_spec(
        {"level": _2P_LEVEL, "players": ["random", "donothing"], "mode": "score"}
    )
    assert len(game.get_current_ranking()) == 2


def test_capitals_mode_game_completes():
    game = _run_spec(
        {"level": _4P_LEVEL, "players": ["donothing"] * 4, "mode": "capitals"}
    )
    assert len(game.get_current_ranking()) == 4


# ---------------------------------------------------------------------------
# 8-tribe tests
# ---------------------------------------------------------------------------


def test_8_tribes_generated_completes():
    """8-tribe procedurally generated game runs to completion."""
    game = _run_spec(
        {"tribes": _TRIBES_8, "players": ["random"] * 8, "mode": "score"}, seed=42
    )
    assert len(game.get_current_ranking()) == 8


def test_8_tribes_generated_has_one_winner():
    game = _run_spec(
        {"tribes": _TRIBES_8, "players": ["random"] * 8, "mode": "score"}, seed=7
    )
    winners = [r for r in game.get_current_ranking() if r.result is RESULT.WIN]
    assert len(winners) == 1


def test_8_tribes_40x40_completes():
    """8-tribe game on the 40×40 hand-crafted level runs to completion."""
    game = _run_spec(
        {"level": _8P_LEVEL, "players": ["random"] * 8, "mode": "score"}, seed=0
    )
    assert len(game.get_current_ranking()) == 8


def test_8_tribes_40x40_scores_nonnegative():
    game = _run_spec(
        {"level": _8P_LEVEL, "players": ["donothing"] * 8, "mode": "score"}, seed=0
    )
    assert all(s >= 0 for s in game.get_scores())
