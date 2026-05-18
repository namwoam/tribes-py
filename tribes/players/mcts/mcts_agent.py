"MCTSAgent: Monte Carlo Tree Search player, ported from MCTSPlayer.java."

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Optional

from tribes.players.agent import Agent
from tribes.players.mcts.node import MCTSNode
from tribes.players.mcts.params import MCTSParams

if TYPE_CHECKING:
    from tribes.actions.action import Action
    from tribes.game.game_state import GameState


class MCTSAgent(Agent):
    """UCT MCTS agent.

    On each call to ``act()``, a Monte Carlo Tree Search is run for up to
    ``params.TIME_BUDGET_MS`` milliseconds (or ``params.MAX_ITERATIONS``
    iterations, whichever comes first).  The action with the most visits at the
    root is returned.

    Parameters
    ----------
    seed:
        RNG seed for reproducibility.
    params:
        ``MCTSParams`` instance; defaults are used when omitted.
    """

    def __init__(self, seed: int, params: Optional[MCTSParams] = None) -> None:
        super().__init__(seed)
        self._rng = random.Random(seed)
        self._params = params or MCTSParams()

    def copy(self) -> MCTSAgent:
        return MCTSAgent(self.seed, self._params)

    # ------------------------------------------------------------------
    # Agent API
    # ------------------------------------------------------------------

    def act(self, gs: GameState) -> Action:
        from tribes.actions.tribe_actions.end_turn import EndTurn

        all_actions = gs.get_all_available_actions()

        # Nothing to decide: only EndTurn is available.
        if len(all_actions) == 1:
            return all_actions[0]

        root_actions = (
            self._determine_root_actions(gs)
            if self._params.PRIORITIZE_ROOT
            else all_actions
        )

        if not root_actions:
            return EndTurn(gs.get_active_tribe_id())

        start_score = gs.get_score(self.player_id)
        root = MCTSNode(self._params, self._rng, gs, self.player_id, root_actions)

        deadline = time.perf_counter() + self._params.TIME_BUDGET_MS / 1000.0
        root.mcts_search(start_score, deadline)

        return root_actions[root.most_visited_action()]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _determine_root_actions(self, gs: GameState) -> list[Action]:
        """Return a curated subset of root actions (exclude Destroy / Disband).

        Falls back to all available actions when nothing survives the filter.
        """
        good = self._all_good_actions(gs)
        return good if good else gs.get_all_available_actions()
