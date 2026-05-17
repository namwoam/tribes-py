"""Main entry point for Tribes-py.

Usage examples
--------------
Run a headless game (auto-generated 2-player map):
    python main.py

Run with a JSON spec file:
    python main.py --level levels/sample_2p.json

Override seed or mode from the CLI:
    python main.py --level levels/sample_4p_generated.json --seed 42 --mode score

Enable the pygame GUI:
    python main.py --level levels/sample_2p.json --gui

Run a tournament via JSON config:
    python main.py --tournament config.json
"""

from __future__ import annotations

import json
import logging
import random as _random
from typing import TYPE_CHECKING

import click

from tribes import constants as C
from tribes.types import GAME_MODE
from tribes.game.game import Game
from tribes.game.game_spec import GameSpec
from tribes.tournament import Tournament, _make_agent

if TYPE_CHECKING:
    from tribes.gui.gui import GUI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _start_gui(game: Game) -> GUI | None:
    try:
        from tribes.gui.gui import GUI

        return GUI(game)
    except ImportError:
        logger.warning("pygame not available – running headless.")
        return None


def run_game_from_spec(spec: GameSpec, with_gui: bool = False) -> None:
    rng = _random.Random(spec.seed)
    resolved = spec.resolve(rng)
    players = [_make_agent(pt, resolved.seed) for pt in resolved.players]

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

    game.run(_start_gui(game) if with_gui else None)


def run_tournament(config_path: str, with_gui: bool = False) -> None:
    from tribes.game.game_spec import parse_tribe

    with open(config_path) as f:
        cfg = json.load(f)

    mode_str = cfg.get("mode", "capitals")
    game_mode = (
        GAME_MODE.CAPITALS if mode_str.lower() == "capitals" else GAME_MODE.SCORE
    )
    repetitions = cfg.get("repetitions", 1)
    shift_tribes = cfg.get("shift_tribes", True)
    C.VERBOSE = cfg.get("verbose", True)

    player_names: list[str] = cfg["players"]
    tribe_names: list[str] = cfg["tribes"]
    if len(player_names) != len(tribe_names):
        raise click.ClickException("Number of players must equal number of tribes.")

    tribes = [parse_tribe(t) for t in tribe_names]
    seeds = [int(s) for s in cfg.get("level_seeds", [-1])]

    t = Tournament(game_mode)
    t.set_players(player_names)
    t.set_tribes(tribes)
    t.set_seeds(seeds)
    t.run(repetitions, shift_tribes, with_gui=with_gui)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--tournament",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    metavar="JSON",
    help="Path to tournament JSON config file.",
)
@click.option(
    "--level",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    metavar="JSON",
    help=(
        "Path to a game-spec JSON file. Omit to auto-generate a 2-player"
        " game. See levels/*.json for examples."
    ),
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed (overrides value in spec).",
)
@click.option(
    "--mode",
    type=click.Choice(["capitals", "score"], case_sensitive=False),
    default=None,
    show_default=False,
    help="Game mode — capitals or score (overrides value in spec).",
)
@click.option("--gui", is_flag=True, help="Enable pygame GUI.")
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
def main(
    tournament: str | None,
    level: str | None,
    seed: int | None,
    mode: str | None,
    gui: bool,
    verbose: bool,
) -> None:
    """Tribes-py game runner."""
    if verbose:
        C.VERBOSE = True

    if tournament:
        run_tournament(tournament, with_gui=gui)
        return

    spec = GameSpec.from_file(level) if level is not None else GameSpec()

    if seed is not None:
        spec.seed = seed
    if mode is not None:
        spec.mode = mode

    run_game_from_spec(spec, with_gui=gui)


if __name__ == "__main__":
    main()
