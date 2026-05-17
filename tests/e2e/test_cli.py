"""CLI integration tests for the main entry point."""

import json

from click.testing import CliRunner

import main
from tribes.game.game_spec import GameSpec


def test_cli_runs_with_spec_file(monkeypatch):
    calls = []

    def fake_run(spec, with_gui):
        calls.append((spec, with_gui))

    monkeypatch.setattr(main, "run_game_from_spec", fake_run)

    result = CliRunner().invoke(main.main, ["--level", "levels/sample_2p.json"])

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    spec, gui = calls[0]
    assert isinstance(spec, GameSpec)
    assert not gui


def test_cli_seed_overrides_spec(monkeypatch):
    calls = []

    def fake_run(spec, with_gui):
        calls.append(spec)

    monkeypatch.setattr(main, "run_game_from_spec", fake_run)

    CliRunner().invoke(main.main, ["--level", "levels/sample_2p.json", "--seed", "99"])

    assert calls[0].seed == 99


def test_cli_mode_overrides_spec(monkeypatch):
    calls = []

    def fake_run(spec, with_gui):
        calls.append(spec)

    monkeypatch.setattr(main, "run_game_from_spec", fake_run)

    CliRunner().invoke(
        main.main, ["--level", "levels/sample_2p.json", "--mode", "score"]
    )

    assert calls[0].mode == "score"


def test_cli_auto_generates_when_no_level(monkeypatch):
    calls = []

    def fake_run(spec, with_gui):
        calls.append(spec)

    monkeypatch.setattr(main, "run_game_from_spec", fake_run)

    result = CliRunner().invoke(main.main, [])

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0].level is None  # no level → auto-generate


def test_cli_gui_flag(monkeypatch):
    calls = []

    def fake_run(spec, with_gui):
        calls.append(with_gui)

    monkeypatch.setattr(main, "run_game_from_spec", fake_run)

    CliRunner().invoke(main.main, ["--gui"])

    assert calls[0] is True


def test_cli_runs_tournament_with_generated_level(tmp_path):
    config_path = tmp_path / "tournament.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "score",
                "repetitions": 1,
                "shift_tribes": True,
                "verbose": False,
                "players": ["do_nothing", "do_nothing"],
                "tribes": ["imperius", "bardur"],
                "level_seeds": [42],
            }
        )
    )

    result = CliRunner().invoke(main.main, ["--tournament", str(config_path)])

    assert result.exit_code == 0, result.output
    assert "--------- RESULTS ---------" in result.output
