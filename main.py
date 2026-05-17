"""Main entry point for Tribes-py.

Usage examples
--------------
Run a single headless game (randomly generated map):
    python main.py

Run with GUI:
    python main.py --gui

Specify tribes for the generated map:
    python main.py --tribes bardur --tribes imperius

Run from a level file:
    python main.py --level levels/sample_level_2p.csv

Run a tournament via JSON config:
    python main.py --tournament config.json
"""

from __future__ import annotations

import json
import logging
import random as _random
import time
from typing import TYPE_CHECKING

import click

from tribes import constants as C
from tribes.types import GAME_MODE, TRIBE as TRIBE_TYPE
from tribes.game.game import Game
from tribes.tournament import Tournament, _make_agent

if TYPE_CHECKING:
    from tribes.gui.gui import GUI

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


def _count_tribes_in_level(level_file: str) -> int:
    with open(level_file) as f:
        lines = [line.rstrip("\n") for line in f]
    count = 0
    for line in lines:
        for token in line.split(","):
            parts = token.strip().split(":")
            if (
                parts[0]
                and parts[0][0] == "c"
                and len(parts) == 2
                and parts[1].isdigit()
            ):
                count += 1
    return count


def _start_gui(game: Game) -> GUI | None:
    try:
        from tribes.gui.gui import GUI

        return GUI(game)
    except ImportError:
        logger.warning("pygame not available – running headless.")
        return None


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
    game.run(_start_gui(game) if with_gui else None)


def run_generated_game(
    player_types: list[str],
    tribes: list[TRIBE_TYPE],
    level_seed: int,
    seed: int,
    game_mode: GAME_MODE,
    with_gui: bool,
) -> None:
    players = [_make_agent(pt, seed) for pt in player_types]
    game = Game()
    game.init_generated(players, level_seed, tribes, seed, game_mode)
    game.run(_start_gui(game) if with_gui else None)


def run_tournament(config_path: str, with_gui: bool = False) -> None:
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
    t.run(repetitions, shift_tribes, with_gui=with_gui)


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
    default=(),
    metavar="TYPE",
    help=(
        "Agent type for each player slot (default: auto-detect from level)."
        ' Repeat for each slot, or pass a JSON array: \'["a1","a2"]\'.'
    ),
)
@click.option(
    "--tribes",
    "tribe_names",
    multiple=True,
    default=(),
    metavar="TRIBE",
    help=(
        "Tribe for each player slot when generating a map (ignored with --level)."
        " Repeat for each slot. Defaults to random tribes."
    ),
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
    tribe_names: tuple[str, ...],
    mode: str,
    seed: int | None,
    gui: bool,
    verbose: bool,
) -> None:
    """Tribes-py game runner."""
    if ctx.args:
        if not player_types:
            raise click.UsageError(f"Unexpected argument(s): {' '.join(ctx.args)}")
        player_types = (*player_types, *ctx.args)

    if len(player_types) == 1:
        try:
            parsed = json.loads(player_types[0])
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                player_types = tuple(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

    if verbose:
        C.VERBOSE = True

    seed = seed if seed is not None else int(time.time() * 1000) & 0xFFFF_FFFF

    if tournament:
        run_tournament(tournament, with_gui=gui)
    elif level is not None:
        game_mode = (
            GAME_MODE.CAPITALS if mode.lower() == "capitals" else GAME_MODE.SCORE
        )
        if not player_types:
            n = _count_tribes_in_level(level)
            players = ["random"] * n
            logger.info("Level has %d tribes; using %d random agents.", n, n)
        else:
            players = list(player_types)
        run_single_game(level, players, seed, game_mode, gui)
    else:
        # No level file — procedurally generate the map.
        game_mode = (
            GAME_MODE.CAPITALS if mode.lower() == "capitals" else GAME_MODE.SCORE
        )
        all_tribes = list(TRIBE_TYPE)
        if tribe_names:
            tribes = [_parse_tribe(t) for t in tribe_names]
            n = len(tribes)
        else:
            n = len(player_types) if player_types else 2
            tribes = _random.sample(all_tribes, k=min(n, len(all_tribes)))
        players = list(player_types) if player_types else ["random"] * n
        if len(players) != len(tribes):
            raise click.ClickException(
                f"Number of --players ({len(players)}) must match"
                f" number of --tribes ({len(tribes)})."
            )
        level_seed = seed
        logger.info(
            "Generating map with seed %d, %d tribes: %s",
            level_seed,
            n,
            [t.name for t in tribes],
        )
        run_generated_game(players, tribes, level_seed, seed, game_mode, gui)


if __name__ == "__main__":
    main()
