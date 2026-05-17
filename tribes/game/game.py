"Game loop, ported from Game.java."

from __future__ import annotations

import logging
import random
import sys
from typing import TYPE_CHECKING, Optional

from tribes import constants as C
from tribes.types import ACTION, GAME_MODE, RESULT

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.players.agent import Agent
    from tribes.game.game_state import GameState
    from tribes.game.board import Board
    from tribes.game.tribe_result import TribeResult
    from tribes.actions.action import Action
    from tribes.actors.tribe import Tribe
    from tribes.gui.gui import GUI


class Game:
    """Manages the full game lifecycle: initialisation, game loop, termination."""

    def __init__(self) -> None:
        self._gs: Optional[GameState] = None
        self._observations: list[GameState] = []
        self._seed: int = 0
        self._rnd: random.Random = random.Random()
        self._players: list[Agent] = []
        self._num_players: int = 0
        self._paused: bool = False

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def init(
        self, players: list[Agent], filename: str, seed: int, game_mode: GAME_MODE
    ) -> None:
        from tribes.game.game_state import GameState as GS

        self._seed = seed
        self._rnd = random.Random(seed)
        self._gs = GS(self._rnd, game_mode)
        self._gs.init(filename)
        self._init_structures(players, len(self._gs.get_tribes()))
        self._update_observations()

    def init_from_lines(
        self,
        players: list[Agent],
        lines: list[str],
        seed: int,
        game_mode: GAME_MODE,
    ) -> None:
        from tribes.game.game_state import GameState as GS

        self._seed = seed
        self._rnd = random.Random(seed)
        self._gs = GS(self._rnd, game_mode)
        self._gs.init_from_lines(lines)
        self._init_structures(players, len(self._gs.get_tribes()))
        self._update_observations()

    def init_generated(
        self,
        players: list[Agent],
        level_seed: int,
        tribes_enum: list,
        seed: int,
        game_mode: GAME_MODE,
    ) -> None:
        """Init with a procedurally generated level."""
        from tribes.game.game_state import GameState as GS

        self._seed = seed
        self._rnd = random.Random(seed)
        self._gs = GS(self._rnd, game_mode)
        self._gs.init_generated(level_seed, tribes_enum)
        self._init_structures(players, tribes_enum)
        self._update_observations()

    def _init_structures(self, players: list[Agent], tribes_or_n) -> None:
        if isinstance(tribes_or_n, int):
            n_tribes = tribes_or_n
        else:
            n_tribes = len(tribes_or_n)

        if len(players) != n_tribes:
            logger.error(
                "Number of tribes (%d) must equal number of players (%d).",
                n_tribes,
                len(players),
            )
            sys.exit(-1)

        self._num_players = len(players)
        self._players = list(players)
        all_ids = list(range(self._num_players))
        for i, p in enumerate(self._players):
            p.set_player_ids(i, all_ids)
        self._observations = [None] * self._num_players  # type: ignore[list-item]

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, gui: Optional[GUI] = None) -> None:
        """Run the game to completion."""
        first_end = True

        while True:
            game_over = self._game_over()

            if first_end and game_over:
                self._terminate()
                first_end = False
                self._print_results()
                if gui is None:
                    break
                # Keep window open until it's closed
                if gui is not None:
                    gui.update(self._gs, None)
                    while not gui.is_closed():
                        gui.pump()
                break

            if not game_over:
                self._tick(gui)
            else:
                if gui is not None:
                    gui.update(self._gs, None)

            if gui is not None:
                if gui.is_closed():
                    break

    # ------------------------------------------------------------------
    # Tick / turn
    # ------------------------------------------------------------------

    def _tick(self, gui: Optional[GUI]) -> None:
        tribes = self._gs.get_tribes()
        for i in range(self._num_players):
            tribe = tribes[i]
            if tribe.get_winner() is not RESULT.INCOMPLETE:
                continue
            self._process_turn(i, tribe, gui)
            if self._game_over():
                return

        self._gs.inc_tick()

    def _process_turn(self, player_id: int, tribe: Tribe, gui: Optional[GUI]) -> None:
        self._gs.init_turn(tribe)
        self._gs.compute_player_actions(tribe)
        self._update_observations()

        agent = self._players[player_id]
        obs = self._observations[player_id]

        continue_turn = True

        while True:
            action: Optional[Action] = None

            if not self._paused and continue_turn:
                action = agent.act(obs)
                continue_turn = (
                    not self._gs.is_turn_ending()
                    and self._gs.exist_available_actions(tribe)
                )

            if action is None and not continue_turn:
                # Auto-end turn
                from tribes.actions.tribe_actions.end_turn import EndTurn

                action = EndTurn(self._gs.get_active_tribe_id())

            if gui is not None and action is not None:
                gui.update(obs, action)

            if action is not None:
                self._gs.next(action)
                self._gs.compute_player_actions(tribe)
                self._update_observations()
                obs = self._observations[player_id]

            if action is not None and action.action_type is ACTION.END_TURN:
                break

            if self._game_over():
                break

        self._gs.end_turn(tribe)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_observations(self) -> None:
        for i in range(self._num_players):
            if C.PLAY_WITH_FULL_OBS:
                self._observations[i] = self._gs.copy(-1)
            else:
                self._observations[i] = self._gs.copy(i)

    def _game_over(self) -> bool:
        return self._gs.game_over()

    def _terminate(self) -> None:
        tribes = self._gs.get_tribes()
        for i in range(self._num_players):
            self._players[i].result(self._gs.copy(), tribes[i].get_score())

    def _print_results(self) -> None:
        ranking = self._gs.get_current_ranking()
        tribes = self._gs.get_board().get_tribes()
        logger.info("Tick %d; Game Results:", self._gs.get_tick())
        for rank, tr in enumerate(ranking, 1):
            tid = tr.id
            agent_name = type(self._players[tid]).__name__
            tribe_type = tribes[tid].get_type().name
            logger.info(
                " #%d: Tribe %s (%s): %s, %d pts; techs=%d, cities=%d, prod=%d",
                rank,
                tribe_type,
                agent_name,
                tr.result.name,
                tr.score,
                tr.num_techs_researched,
                tr.num_cities,
                tr.production,
            )
        if C.VERBOSE:
            self._print_results_stdout()

    def _print_results_stdout(self) -> None:
        ranking = self._gs.get_current_ranking()
        tribes = self._gs.get_board().get_tribes()
        print(f"{self._gs.get_tick()}; Game Results:")
        for rank, tr in enumerate(ranking, 1):
            tid = tr.id
            agent_name = type(self._players[tid]).__name__
            tribe_type = tribes[tid].get_type().name
            print(
                f" #{rank}: Tribe {tribe_type} ({agent_name}): "
                f"{tr.result.name}, {tr.score} points; "
                f"#tech: {tr.num_techs_researched}, "
                f"#cities: {tr.num_cities}, production: {tr.production}"
            )

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_board(self) -> Board:
        return self._gs.get_board()

    def get_players(self) -> list[Agent]:
        return self._players

    def get_winner_status(self) -> list[RESULT]:
        return [self._gs.get_tribes()[i].get_winner() for i in range(self._num_players)]

    def get_scores(self) -> list[int]:
        return [self._gs.get_tribes()[i].get_score() for i in range(self._num_players)]

    def get_current_ranking(self) -> list[TribeResult]:
        return self._gs.get_current_ranking()

    def get_game_state(self) -> GameState:
        return self._gs

    def set_paused(self, paused: bool) -> None:
        self._paused = paused

    def is_paused(self) -> bool:
        return self._paused
