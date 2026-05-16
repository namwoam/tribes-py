"""Main entry point for Tribes-py.

Usage examples
--------------
Run a single headless game:
    python main.py

Run with GUI:
    python main.py --gui

Run a tournament via JSON config:
    python main.py --tournament config.json
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import click

from tribes import constants as C
from tribes.types import GAME_MODE, TRIBE as TRIBE_TYPE
from tribes.game.game import Game
from tribes.tournament import Tournament, _make_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Quick-start helpers
# ---------------------------------------------------------------------------


def _parse_tribe(name: str) -> TRIBE_TYPE:
    mapping = {
        "xin xi": TRIBE_TYPE.XIN_XI,
        "xin_xi": TRIBE_TYPE.XIN_XI,
        "imperius": TRIBE_TYPE.IMPERIUS,
        "bardur": TRIBE_TYPE.BARDUR,
        "oumaji": TRIBE_TYPE.OUMAJI,
        "kickoo": TRIBE_TYPE.KICKOO,
        "hoodrick": TRIBE_TYPE.HOODRICK,
        "luxidoor": TRIBE_TYPE.LUXIDOOR,
        "vengir": TRIBE_TYPE.VENGIR,
        "zebasi": TRIBE_TYPE.ZEBASI,
        "ai-mo": TRIBE_TYPE.AI_MO,
        "ai_mo": TRIBE_TYPE.AI_MO,
        "quetzali": TRIBE_TYPE.QUETZALI,
        "yadakk": TRIBE_TYPE.YADAKK,
    }
    key = name.strip().lower()
    if key not in mapping:
        raise ValueError(f"Unknown tribe: {name!r}")
    return mapping[key]


def run_single_game(
    level_file: str,
    player_types: list[str],
    seed: int,
    game_mode: GAME_MODE,
    with_gui: bool,
) -> None:
    players = [_make_agent(pt, seed) for pt in player_types]
    game = Game()
    game.init(players, level_file, seed, game_mode)

    gui = None
    if with_gui:
        try:
            from tribes.gui.gui import GUI

            gui = GUI(game)
        except ImportError:
            logger.warning("pygame not available – running headless.")

    game.run(gui)


def run_tournament(config_path: str) -> None:
    with open(config_path) as f:
        cfg = json.load(f)

    game_mode = (
        GAME_MODE.CAPITALS
        if cfg.get("Game Mode", "Capitals").lower() == "capitals"
        else GAME_MODE.SCORE
    )
    repetitions = cfg.get("Repetitions", 1)
    shift_tribes = cfg.get("Shift Tribes", True)
    C.VERBOSE = cfg.get("Verbose", True)

    player_names: list[str] = cfg["Players"]
    tribe_names: list[str] = cfg["Tribes"]
    if len(player_names) != len(tribe_names):
        raise click.ClickException("Number of players must equal number of tribes.")

    tribes = [_parse_tribe(t) for t in tribe_names]
    raw_seeds = cfg.get("Level Seeds", [-1])
    seeds = [int(s) for s in raw_seeds]

    t = Tournament(game_mode)
    t.set_players(player_names)
    t.set_tribes(tribes)
    t.set_seeds(seeds)
    t.run(repetitions, shift_tribes)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command(
    context_settings={
        "allow_extra_args": True,
        "help_option_names": ["-h", "--help"],
    }
)
@click.option(
    "--tournament",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    metavar="JSON",
    help="Path to tournament JSON config file.",
)
@click.option(
    "--level",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    metavar="FILE",
    help="Level file to load for a single game.",
)
@click.option(
    "--players",
    "player_types",
    multiple=True,
    default=("random", "random"),
    metavar="TYPE",
    show_default="random, random",
    help="Agent type for a single game. Repeat for each player slot.",
)
@click.option(
    "--mode",
    type=click.Choice(["capitals", "score"], case_sensitive=False),
    default="capitals",
    show_default=True,
    help="Game mode.",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed.",
)
@click.option(
    "--gui",
    is_flag=True,
    help="Enable pygame GUI.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output.",
)
@click.pass_context
def main(
    ctx: click.Context,
    tournament: str | None,
    level: str | None,
    player_types: tuple[str, ...],
    mode: str,
    seed: int | None,
    gui: bool,
    verbose: bool,
) -> None:
    """Tribes-py game runner."""
    if ctx.args:
        if player_types == ("random", "random"):
            raise click.UsageError(f"Unexpected argument(s): {' '.join(ctx.args)}")
        player_types = (*player_types, *ctx.args)

    if verbose:
        C.VERBOSE = True

    seed = seed if seed is not None else int(time.time() * 1000) & 0xFFFF_FFFF

    if tournament:
        run_tournament(tournament)
    else:
        if level is None:
            # Find first available level file
            candidates = sorted(Path(".").rglob("*.csv"))
            level_candidates = [str(p) for p in candidates if "level" in p.name.lower()]
            if not level_candidates:
                level_candidates = [str(p) for p in candidates]
            if not level_candidates:
                raise click.ClickException("No level file found. Use --level <file>.")
            level = level_candidates[0]
            logger.info("Using level file: %s", level)

        game_mode = (
            GAME_MODE.CAPITALS if mode.lower() == "capitals" else GAME_MODE.SCORE
        )
        run_single_game(level, list(player_types), seed, game_mode, gui)


if __name__ == "__main__":
    main()
