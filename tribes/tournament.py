"Tournament runner, ported from Tournament.java."

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tribes import constants as C
from tribes.types import GAME_MODE, TRIBE as TRIBE_TYPE

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.game import Game
    from tribes.players.agent import Agent


@dataclass
class StatSummary:
    values: list[float] = field(default_factory=list)

    def add(self, v: float) -> None:
        self.values.append(v)

    def sum(self) -> float:
        return sum(self.values)

    def mean(self) -> float:
        return self.sum() / len(self.values) if self.values else 0.0

    def n(self) -> int:
        return len(self.values)


@dataclass
class ParticipantStats:
    participant_id: int
    player_type: str
    v: StatSummary = field(default_factory=StatSummary)  # victories
    s: StatSummary = field(default_factory=StatSummary)  # score
    t: StatSummary = field(default_factory=StatSummary)  # techs
    c: StatSummary = field(default_factory=StatSummary)  # cities
    p: StatSummary = field(default_factory=StatSummary)  # production
    d: StatSummary = field(default_factory=StatSummary)  # wars
    r: StatSummary = field(default_factory=StatSummary)  # stars


class Tournament:
    """Runs a round-robin tournament between a fixed set of agents."""

    def __init__(self, game_mode: GAME_MODE = GAME_MODE.CAPITALS) -> None:
        self._game_mode = game_mode
        self._player_types: list[str] = []
        self._tribes: list[TRIBE_TYPE] = []
        self._seeds: list[int] = []
        self._stats: list[ParticipantStats] = []

    def set_players(self, player_types: list[str]) -> None:
        self._player_types = list(player_types)
        self._stats = [ParticipantStats(i, pt) for i, pt in enumerate(player_types)]

    def set_tribes(self, tribes: list[TRIBE_TYPE]) -> None:
        self._tribes = list(tribes)

    def set_seeds(self, seeds: list[int]) -> None:
        self._seeds = list(seeds)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(
        self, repetitions: int = 1, shift_tribes: bool = True, with_gui: bool = False
    ) -> None:
        starter = 0
        total = len(self._seeds) * repetitions

        for seed_idx, level_seed in enumerate(self._seeds):
            if level_seed == -1:
                level_seed = int(time.time() * 1000) + random.randint(0, 999)
            print(f"**** Playing level with seed {level_seed} ****")

            rep = 0
            attempts = 0
            while rep < repetitions:
                assignment: dict[TRIBE_TYPE, int] = {}
                ordered_types: list[str] = []
                ordered_tribes: list[TRIBE_TYPE] = []

                next_idx = starter
                n = len(self._player_types)
                for slot in range(n):
                    pt = self._player_types[next_idx % n]
                    tribe = self._tribes[slot]
                    assignment[tribe] = next_idx % n
                    ordered_types.append(pt)
                    ordered_tribes.append(tribe)
                    next_idx += 1

                print(
                    f"Playing [{', '.join(ordered_types)}] "
                    f"({seed_idx * repetitions + rep + 1}/{total})"
                )

                try:
                    game = self._prepare_game(ordered_tribes, level_seed, ordered_types)
                    gui = None
                    if with_gui:
                        try:
                            from tribes.gui.gui import GUI

                            gui = GUI(game)
                        except ImportError:
                            logger.warning("pygame not available – running headless.")
                    game.run(gui)
                    self._record_results(game, assignment)
                    if shift_tribes:
                        starter = (starter + 1) % n
                    rep += 1
                    attempts = 0
                except Exception as exc:
                    attempts += 1
                    if attempts >= 3:
                        logger.exception("Error running game; giving up: %s", exc)
                        raise
                    logger.exception("Error running game, retrying: %s", exc)

        self._print_results()

    def _prepare_game(
        self, tribes: list[TRIBE_TYPE], level_seed: int, player_types: list[str]
    ) -> "Game":
        from tribes.game.game import Game
        from tribes.tournament import _make_agent

        game_seed = int(time.time() * 1000)
        if C.VERBOSE:
            print(f"Game seed: {game_seed}, Level seed: {level_seed}")

        players = [_make_agent(pt, game_seed) for pt in player_types]
        game = Game()
        game.init_generated(players, level_seed, tribes, game_seed, self._game_mode)
        return game

    def _record_results(self, game: "Game", assignment: dict[TRIBE_TYPE, int]) -> None:
        from tribes.types import RESULT

        ranking = game.get_current_ranking()
        board = game.get_board()
        for tr in ranking:
            tribe_obj = board.get_tribe(tr.id)
            tribe_type = tribe_obj.get_type()
            pid = assignment[tribe_type]
            stat = self._stats[pid]
            stat.v.add(1 if tr.result is RESULT.WIN else 0)
            stat.s.add(tr.score)
            stat.t.add(tr.num_techs_researched)
            stat.c.add(tr.num_cities)
            stat.p.add(tr.production)
            stat.d.add(tr.num_wars)
            stat.r.add(tr.num_stars)

    def _print_results(self) -> None:
        sorted_stats = sorted(
            self._stats,
            key=lambda s: (
                -s.v.sum(),
                -s.s.mean(),
                -s.t.mean(),
                -s.c.mean(),
                -s.p.mean(),
                -s.d.mean(),
                -s.r.mean(),
            ),
        )
        print("--------- RESULTS ---------")
        for st in sorted_stats:
            w = int(st.v.sum())
            n = st.v.n()
            pct = 100.0 * w / n if n > 0 else 0.0
            print(
                f"[N:{n}];[%:{pct:.2f}];[W:{w}];"
                f"[S:{st.s.mean():.2f}];[T:{st.t.mean():.2f}];"
                f"[C:{st.c.mean():.2f}];[P:{st.p.mean():.2f}];"
                f"[D:{st.d.mean():.2f}];[R:{st.r.mean():.2f}];"
                f"[Player:{st.participant_id}:{st.player_type}]"
            )


# ---------------------------------------------------------------------------
# Factory helper (analogous to Run.getAgent in Java)
# ---------------------------------------------------------------------------


def _make_agent(player_type: str, seed: int) -> "Agent":
    from tribes.players.random_agent import RandomAgent
    from tribes.players.do_nothing_agent import DoNothingAgent
    from tribes.players.simple_agent import SimpleAgent

    pt = player_type.lower()
    if pt in ("random",):
        return RandomAgent(seed)
    if pt in ("donothing", "do_nothing", "do nothing"):
        return DoNothingAgent(seed)
    if pt in ("simple", "rule based", "rule_based"):
        return SimpleAgent(seed)
    if pt in ("mcts",):
        from tribes.players.mcts import MCTSAgent

        return MCTSAgent(seed)
    raise ValueError(f"Unknown player type: {player_type!r}")
