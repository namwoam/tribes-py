"MCTS tree node plus game-state advancement helpers."

from __future__ import annotations

import math
import random
import time
from typing import TYPE_CHECKING, Optional

from tribes.types import ACTION, RESULT

if TYPE_CHECKING:
    from tribes.players.mcts.params import MCTSParams
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action


# ---------------------------------------------------------------------------
# Game-state helpers (all modify gs in-place; caller is responsible for copies)
# ---------------------------------------------------------------------------


def _play_opponent_turn(gs: GameState, tribe_id: int, rng: random.Random) -> None:
    """Play one complete random turn for tribe_id, modifying gs in-place."""
    from tribes.actions.tribe_actions.end_turn import EndTurn

    tribe = gs.get_tribe(tribe_id)
    if tribe.get_winner() is not RESULT.INCOMPLETE:
        return

    gs.init_turn(tribe)
    gs.compute_player_actions(tribe)

    while True:
        actions = gs.get_all_available_actions()
        action: Action = rng.choice(actions) if actions else EndTurn(tribe_id)

        gs.next(action)
        gs.compute_player_actions(tribe)

        if action.action_type is ACTION.END_TURN:
            break
        if not gs.exist_available_actions(tribe) or gs.is_turn_ending():
            gs.next(EndTurn(tribe_id))
            break
        if gs.game_over():
            break

    gs.end_turn(tribe)


def _step_action(
    gs: GameState, action: Action, player_id: int, rng: random.Random
) -> None:
    """Execute one action for player_id and, if the turn ends, auto-advance opponents.

    After this call gs has player_id's next-turn actions computed (or is game-over).
    Mirrors the gym_env.step() turn-management logic.
    """
    from tribes.actions.tribe_actions.end_turn import EndTurn

    tribe = gs.get_tribe(player_id)
    gs.next(action)
    gs.compute_player_actions(tribe)

    is_end = action.action_type is ACTION.END_TURN
    has_more = gs.exist_available_actions(tribe)

    if is_end or not has_more:
        if not is_end:
            # Force-end the turn when no actions remain.
            gs.next(EndTurn(tribe.tribe_id))
        gs.end_turn(tribe)
        gs.game_over()

        if not gs.is_game_over():
            n = len(gs.get_tribes())
            for opp_id in range(n):
                if opp_id == player_id or gs.is_game_over():
                    continue
                _play_opponent_turn(gs, opp_id, rng)
                gs.game_over()

        if not gs.is_game_over():
            gs.inc_tick()
            # Re-initialise player_id's turn so the node has ready actions.
            p_tribe = gs.get_tribe(player_id)
            if p_tribe.get_winner() is RESULT.INCOMPLETE:
                gs.init_turn(p_tribe)
                gs.compute_player_actions(p_tribe)


def _evaluate(gs: GameState, player_id: int, start_score: int) -> float:
    """Return a value in [0, 1]: 1.0 = winning/leading, 0.0 = losing/trailing.

    Terminal states return exact win/loss; non-terminal states return the agent's
    share of the total score accumulated so far.
    """
    if gs.is_game_over():
        result = gs.get_tribe(player_id).get_winner()
        if result is RESULT.WIN:
            return 1.0
        if result is RESULT.LOSS:
            return 0.0
        return 0.5

    n = len(gs.get_tribes())
    scores = [gs.get_score(i) for i in range(n)]
    total = sum(scores)
    if total == 0:
        return 0.5
    return scores[player_id] / total


# ---------------------------------------------------------------------------
# MCTS tree node
# ---------------------------------------------------------------------------


class MCTSNode:
    """One node in the MCTS tree.

    ``gs`` is the game state **after** the action that created this node has been
    applied (and opponents have been auto-played if the player's turn ended).
    ``actions`` are the actions available to player_id from that state.
    """

    __slots__ = (
        "params",
        "rng",
        "gs",
        "player_id",
        "actions",
        "parent",
        "action_idx",
        "children",
        "visits",
        "total_value",
        "_untried",
    )

    def __init__(
        self,
        params: MCTSParams,
        rng: random.Random,
        gs: GameState,
        player_id: int,
        actions: list[Action],
        parent: Optional[MCTSNode] = None,
        action_idx: int = -1,
    ) -> None:
        self.params = params
        self.rng = rng
        self.gs = gs
        self.player_id = player_id
        self.actions = actions
        self.parent = parent
        self.action_idx = action_idx

        n = len(actions)
        self.children: list[Optional[MCTSNode]] = [None] * n
        self.visits: int = 0
        self.total_value: float = 0.0
        self._untried: list[int] = list(range(n))
        rng.shuffle(self._untried)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    def is_terminal(self) -> bool:
        return self.gs.is_game_over() or not self.actions

    def is_fully_expanded(self) -> bool:
        return len(self._untried) == 0

    # ------------------------------------------------------------------
    # UCT
    # ------------------------------------------------------------------

    def _uct(self) -> float:
        if self.visits == 0:
            return float("inf")
        exploit = self.total_value / self.visits
        explore = self.params.K * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploit + explore

    def _best_child_uct(self) -> MCTSNode:
        return max((c for c in self.children if c is not None), key=lambda c: c._uct())

    # ------------------------------------------------------------------
    # Four MCTS phases
    # ------------------------------------------------------------------

    def select(self) -> MCTSNode:
        node = self
        while not node.is_terminal() and node.is_fully_expanded():
            node = node._best_child_uct()
        return node

    def expand(self) -> MCTSNode:
        idx = self._untried.pop()
        action = self.actions[idx]

        next_gs = self.gs.copy(-1)
        _step_action(next_gs, action, self.player_id, self.rng)

        next_actions = next_gs.get_all_available_actions()
        child = MCTSNode(
            self.params,
            self.rng,
            next_gs,
            self.player_id,
            next_actions,
            parent=self,
            action_idx=idx,
        )
        self.children[idx] = child
        return child

    def rollout(self, start_score: int) -> float:
        gs = self.gs.copy(-1)
        for _ in range(self.params.ROLLOUT_DEPTH):
            if gs.is_game_over():
                break
            actions = gs.get_all_available_actions()
            if not actions:
                break
            action = self.rng.choice(actions)
            _step_action(gs, action, self.player_id, self.rng)
        return _evaluate(gs, self.player_id, start_score)

    def backpropagate(self, value: float) -> None:
        node: Optional[MCTSNode] = self
        while node is not None:
            node.visits += 1
            node.total_value += value
            node = node.parent

    # ------------------------------------------------------------------
    # Search entry-point
    # ------------------------------------------------------------------

    def mcts_search(self, start_score: int, deadline: float) -> None:
        """Run UCT iterations until *deadline* (perf_counter) or MAX_ITERATIONS."""
        iters = 0
        while time.perf_counter() < deadline and iters < self.params.MAX_ITERATIONS:
            node = self.select()
            if not node.is_terminal():
                node = node.expand()
            value = (
                _evaluate(node.gs, node.player_id, start_score)
                if node.is_terminal()
                else node.rollout(start_score)
            )
            node.backpropagate(value)
            iters += 1

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------

    def most_visited_action(self) -> int:
        """Return the index (into self.actions) of the most-visited child."""
        best_idx, best_visits = 0, -1
        for i, child in enumerate(self.children):
            if child is not None and child.visits > best_visits:
                best_visits = child.visits
                best_idx = i
        return best_idx
