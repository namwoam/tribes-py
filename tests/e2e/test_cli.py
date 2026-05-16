"""CLI integration tests for the main entry point."""

import json

from click.testing import CliRunner

from tribes.types import GAME_MODE

import main


def test_cli_runs_single_game_with_click_player_options(monkeypatch):
    calls = []

    def fake_run_single_game(level_file, player_types, seed, game_mode, with_gui):
        calls.append((level_file, player_types, seed, game_mode, with_gui))

    monkeypatch.setattr(main, "run_single_game", fake_run_single_game)

    result = CliRunner().invoke(
        main.main,
        [
            "--level",
            "levels/sample_level.csv",
            "--players",
            "random",
            "--players",
            "simple",
            "--mode",
            "score",
            "--seed",
            "42",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            "levels/sample_level.csv",
            ["random", "simple"],
            42,
            GAME_MODE.SCORE,
            False,
        )
    ]


def test_cli_keeps_legacy_players_argument_form(monkeypatch):
    calls = []

    def fake_run_single_game(level_file, player_types, seed, game_mode, with_gui):
        calls.append((level_file, player_types, seed, game_mode, with_gui))

    monkeypatch.setattr(main, "run_single_game", fake_run_single_game)

    result = CliRunner().invoke(
        main.main,
        [
            "--level",
            "levels/sample_level.csv",
            "--players",
            "random",
            "simple",
            "--seed",
            "42",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            "levels/sample_level.csv",
            ["random", "simple"],
            42,
            GAME_MODE.CAPITALS,
            False,
        )
    ]


def test_cli_rejects_unexpected_positional_arguments():
    result = CliRunner().invoke(main.main, ["unexpected"])

    assert result.exit_code == 2
    assert "Unexpected argument(s): unexpected" in result.output


def test_cli_runs_tournament_with_generated_level(tmp_path):
    config_path = tmp_path / "tournament.json"
    config_path.write_text(
        json.dumps(
            {
                "Game Mode": "Score",
                "Repetitions": 1,
                "Shift Tribes": True,
                "Verbose": False,
                "Players": ["do_nothing", "do_nothing"],
                "Tribes": ["Imperius", "Bardur"],
                "Level Seeds": [42],
            }
        )
    )

    result = CliRunner().invoke(main.main, ["--tournament", str(config_path)])

    assert result.exit_code == 0, result.output
    assert "--------- RESULTS ---------" in result.output
