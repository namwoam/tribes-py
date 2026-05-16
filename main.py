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

import argparse
import json
import logging
import sys
import time
from pathlib import Path

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


def run_single_game(level_file: str, player_types: list[str],
                    seed: int, game_mode: GAME_MODE, with_gui: bool) -> None:
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

    game_mode = (GAME_MODE.CAPITALS
                 if cfg.get("Game Mode", "Capitals").lower() == "capitals"
                 else GAME_MODE.SCORE)
    repetitions = cfg.get("Repetitions", 1)
    shift_tribes = cfg.get("Shift Tribes", True)
    C.VERBOSE = cfg.get("Verbose", True)

    player_names: list[str] = cfg["Players"]
    tribe_names: list[str] = cfg["Tribes"]
    if len(player_names) != len(tribe_names):
        sys.exit("Number of players must equal number of tribes.")

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

def main() -> None:
    parser = argparse.ArgumentParser(description="Tribes-py game runner")
    parser.add_argument(
        "--tournament", metavar="JSON", default=None,
        help="Path to tournament JSON config file.",
    )
    parser.add_argument(
        "--level", metavar="FILE", default=None,
        help="Level file to load for a single game.",
    )
    parser.add_argument(
        "--players", nargs="+", default=["random", "random"],
        help="Agent types for a single game (e.g. random simple).",
    )
    parser.add_argument(
        "--mode", choices=["capitals", "score"], default="capitals",
        help="Game mode.",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed.",
    )
    parser.add_argument(
        "--gui", action="store_true",
        help="Enable pygame GUI.",
    )
    parser.add_argument(
        "--verbose", action="store_true", default=False,
        help="Enable verbose output.",
    )
    args = parser.parse_args()

    if args.verbose:
        C.VERBOSE = True

    seed = args.seed if args.seed is not None else int(time.time() * 1000) & 0xFFFF_FFFF

    if args.tournament:
        run_tournament(args.tournament)
    else:
        level = args.level
        if level is None:
            # Find first available level file
            candidates = sorted(Path(".").rglob("*.txt"))
            level_candidates = [str(p) for p in candidates if "level" in p.name.lower()]
            if not level_candidates:
                level_candidates = [str(p) for p in candidates]
            if not level_candidates:
                sys.exit("No level file found. Use --level <file>.")
            level = level_candidates[0]
            logger.info("Using level file: %s", level)

        game_mode = GAME_MODE.CAPITALS if args.mode == "capitals" else GAME_MODE.SCORE
        run_single_game(level, args.players, seed, game_mode, args.gui)


if __name__ == "__main__":
    main()
