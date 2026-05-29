"Curriculum learning wrapper for TribesEnv."

from __future__ import annotations

import copy
import random as _random
from collections import deque
from dataclasses import dataclass
from typing import Optional

import numpy as np
import gymnasium as gym

from tribes.gym_env import TribesEnv, game_state_to_obs, MAX_ACTIONS
from tribes.players.agent import Agent
from tribes.players.random_agent import RandomAgent
from tribes.players.simple_agent import SimpleAgent
from tribes.types import TRIBE as TRIBE_TYPE, RESULT

# ---------------------------------------------------------------------------
# Curriculum definition
# ---------------------------------------------------------------------------


@dataclass
class Stage:
    """One step in the curriculum."""

    name: str
    n_tribes: int
    opp_type: str  # "random" | "simple" | "mixed" | "self" | "handicapped"
    min_steps: int  # env steps before advancement is even considered
    win_threshold: float  # rolling win-rate needed to advance (0 = final stage)
    # Fraction of episodes that use SimpleAgent when opp_type == "mixed".
    # 0.0 = all random, 1.0 = all simple.
    mix_ratio: float = 0.5
    # Probability that a "handicapped" SimpleAgent takes a random action instead.
    # 0.0 = full SimpleAgent, 1.0 = fully random.
    handicap: float = 0.0


#: Full 8-tribe pool used by the curriculum (all tribes the game supports).
DEFAULT_TRIBES_POOL: list = [
    TRIBE_TYPE.IMPERIUS,
    TRIBE_TYPE.BARDUR,
    TRIBE_TYPE.OUMAJI,
    TRIBE_TYPE.KICKOO,
    TRIBE_TYPE.HOODRICK,
    TRIBE_TYPE.LUXIDOOR,
    TRIBE_TYPE.VENGIR,
    TRIBE_TYPE.ZEBASI,
]

#: Curriculum: random → mixed → handicapped-simple → simple → self-play, 2→8 players.
#:
#: Key design choices
#: ------------------
#: * mixed-Np uses mix_ratio=0.3 so 70 % of opponents are still random — a gentle
#:   introduction to purposeful play before fully handicapped stages.
#: * Advancement thresholds decrease as player count grows (harder to win outright
#:   in large lobbies where random chance of placing 1st drops).
#: * simple-* thresholds are low on purpose: the point is exposure, not mastery —
#:   the self-play stages are where the policy truly improves.
DEFAULT_CURRICULUM: list[Stage] = [
    # ── Phase 1: Random opponents, 2 → 8 players ────────────────────────────
    Stage("random-2p", 2, "random", 20_000, 0.80),
    Stage("random-3p", 3, "random", 25_000, 0.80),
    Stage("random-4p", 4, "random", 30_000, 0.80),
    Stage("random-6p", 6, "random", 35_000, 0.80),
    Stage("random-8p", 8, "random", 40_000, 0.70),
    # ── Phase 1.5: Mixed bridge — low simple ratio keeps it achievable ───────
    Stage("mixed-2p",  2, "mixed", 20_000, 0.75, mix_ratio=0.3),
    Stage("mixed-3p",  3, "mixed", 25_000, 0.75, mix_ratio=0.3),
    Stage("mixed-4p",  4, "mixed", 30_000, 0.70, mix_ratio=0.3),
    Stage("mixed-6p",  6, "mixed", 35_000, 0.60, mix_ratio=0.3),
    Stage("mixed-8p",  8, "mixed", 40_000, 0.55, mix_ratio=0.3),
    # ── Phase 2a: Handicapped SimpleAgent (50 % random), 2 → 8 players ──────
    # Thresholds decrease with player count: in an N-player game the agent
    # must beat N-1 opponents, so the achievable win rate shrinks accordingly.
    Stage("simple-easy-2p", 2, "handicapped", 30_000, 0.65, handicap=0.5),
    Stage("simple-easy-3p", 3, "handicapped", 35_000, 0.55, handicap=0.5),
    Stage("simple-easy-4p", 4, "handicapped", 40_000, 0.50, handicap=0.5),
    Stage("simple-easy-6p", 6, "handicapped", 45_000, 0.45, handicap=0.5),
    Stage("simple-easy-8p", 8, "handicapped", 50_000, 0.40, handicap=0.5),
    # ── Phase 2b: Full SimpleAgent, 2 → 8 players ───────────────────────────
    Stage("simple-2p", 2, "simple", 40_000, 0.65),
    Stage("simple-3p", 3, "simple", 45_000, 0.55),
    Stage("simple-4p", 4, "simple", 50_000, 0.50),
    Stage("simple-6p", 6, "simple", 55_000, 0.45),
    Stage("simple-8p", 8, "simple", 60_000, 0.40),
    # ── Phase 3: Self-play, 2 → 8 players ───────────────────────────────────
    Stage("self-2p", 2, "self", 50_000, 0.65),
    Stage("self-3p", 3, "self", 55_000, 0.55),
    Stage("self-4p", 4, "self", 60_000, 0.45),
    Stage("self-6p", 6, "self", 65_000, 0.40),
    Stage("self-8p", 8, "self", 0, 0.0),   # final stage
]


# ---------------------------------------------------------------------------
# Self-play opponent
# ---------------------------------------------------------------------------


class HandicappedAgent(Agent):
    """Wraps a base agent; takes a random legal action with probability `handicap`.

    Used to create a difficulty slope between the mixed and full-simple stages.
    """

    def __init__(self, base_agent: Agent, handicap: float, seed: int) -> None:
        super().__init__(seed)
        self._base = base_agent
        self._handicap = handicap
        self._rng = _random.Random(seed)

    def act(self, gs):
        if self._rng.random() < self._handicap:
            actions = gs.get_all_available_actions()
            if actions:
                return self._rng.choice(actions)
        return self._base.act(gs)

    def copy(self) -> "HandicappedAgent":
        return HandicappedAgent(
            self._base.copy(), self._handicap, self._rng.randint(0, 2**31)
        )


class SelfPlayAgent(Agent):
    """Opponent that plays using a frozen snapshot of the learner's SB3 policy.

    The snapshot is a deepcopy of the `MaskablePPO.policy` object and is
    updated by `CurriculumEnv._sync_self_play()` on a fixed update schedule.
    """

    def __init__(self, seed: int, policy, n_tribes: int) -> None:
        super().__init__(seed)
        self._policy = policy
        self._n_tribes = n_tribes

    def act(self, gs):  # gs is a GameState, returns an Action
        # Use self.player_id as perspective so the relative unit_tribe encoding
        # is correct for this opponent's point of view.
        obs = game_state_to_obs(gs, perspective=self.player_id)
        obs_batched = {k: v[np.newaxis] for k, v in obs.items()}

        legal = gs.get_all_available_actions()
        if not legal:
            from tribes.actions.tribe_actions.end_turn import EndTurn

            return EndTurn(gs.get_active_tribe_id())

        mask = np.zeros(MAX_ACTIONS, dtype=bool)
        mask[: len(legal)] = True

        action, _ = self._policy.predict(
            obs_batched,
            action_masks=mask[np.newaxis],
            deterministic=False,
        )

        idx = min(int(action[0]), len(legal) - 1)
        return legal[idx]

    def copy(self) -> "SelfPlayAgent":
        return SelfPlayAgent(self.seed, self._policy, self._n_tribes)


# ---------------------------------------------------------------------------
# Curriculum environment
# ---------------------------------------------------------------------------


class CurriculumEnv(gym.Env):
    """Gymnasium wrapper that advances through a curriculum of TribesEnv stages.

    Stages are defined by a list of :class:`Stage` objects.  After completing
    at least ``stage.min_steps`` env steps **and** achieving a rolling win-rate
    ≥ ``stage.win_threshold`` (over the last ``outcome_window`` episodes), the
    curriculum automatically advances to the next stage.

    Progression
    -----------
    Phase 1 – RandomAgent opponents (2 → 4 tribes / 11 → 16-tile maps)
    Phase 2 – SimpleAgent opponents  (2 → 4 tribes)
    Phase 3 – Self-play              (2 → 4 tribes)

    Self-play
    ---------
    When entering a self-play stage a frozen deepcopy of the learner's SB3
    policy is taken.  The snapshot is refreshed every ``self_play_sync_interval``
    calls to :meth:`notify_update`, which should be triggered once per gradient
    update (e.g. from an SB3 ``BaseCallback``).
    """

    metadata: dict = {"render_modes": []}

    def __init__(
        self,
        stages: Optional[list[Stage]] = None,
        tribes_pool: Optional[list] = None,
        seed: int = 0,
        outcome_window: int = 50,
        self_play_sync_interval: int = 20,
    ) -> None:
        super().__init__()
        self._stages = stages or DEFAULT_CURRICULUM
        self._tribes_pool = tribes_pool or DEFAULT_TRIBES_POOL
        self._seed = seed
        self._outcome_window = outcome_window
        self._self_play_sync_interval = self_play_sync_interval

        self._stage_idx: int = 0
        self._stage_steps: int = 0
        self._updates_in_stage: int = 0
        self._outcomes: deque[float] = deque(maxlen=outcome_window)
        self._self_play_snapshot = None  # frozen SB3 policy object
        self._mix_rng: _random.Random = _random.Random(seed + 9999)

        self._env: TribesEnv = self._build_env()
        self.observation_space = self._env.observation_space
        self.action_space = self._env.action_space

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_stage(self) -> Stage:
        return self._stages[self._stage_idx]

    @property
    def win_rate(self) -> float:
        return float(np.mean(list(self._outcomes))) if self._outcomes else 0.0

    # ------------------------------------------------------------------
    # Gymnasium interface
    # ------------------------------------------------------------------

    def reset(self, **kwargs):
        # For mixed stages, randomly assign the opponent for this episode so the
        # agent is gradually exposed to heuristic play without a hard cutover.
        if self.current_stage.opp_type == "mixed":
            if self._mix_rng.random() < self.current_stage.mix_ratio:
                self._env._opponent_cls = SimpleAgent
            else:
                self._env._opponent_cls = RandomAgent
        obs, info = self._env.reset(**kwargs)
        info["curriculum_stage"] = self.current_stage.name
        info["win_rate"] = round(self.win_rate, 3)
        return obs, info

    def step(self, action):
        obs, reward, terminated, truncated, info = self._env.step(action)
        self._stage_steps += 1

        if terminated or truncated:
            result = self._env._gs.get_tribe(0).get_winner()
            self._outcomes.append(1.0 if result is RESULT.WIN else 0.0)
            if self._should_advance():
                self._advance_stage()

        info["curriculum_stage"] = self.current_stage.name
        info["win_rate"] = round(self.win_rate, 3)
        return obs, reward, terminated, truncated, info

    def action_masks(self) -> np.ndarray:
        return self._env.action_masks()

    def render(self):
        pass

    # ------------------------------------------------------------------
    # Called by the training callback after each gradient update
    # ------------------------------------------------------------------

    def notify_update(self, policy=None, update_num: int = 0) -> None:
        """Sync self-play snapshot on schedule.

        Parameters
        ----------
        policy:
            The learner's current SB3 policy object (``model.policy``).
        update_num:
            Running count of gradient updates (used for logging only).
        """
        self._updates_in_stage += 1
        if (
            self.current_stage.opp_type == "self"
            and policy is not None
            and self._updates_in_stage % self._self_play_sync_interval == 0
        ):
            self._sync_self_play(policy)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _should_advance(self) -> bool:
        if self._stage_idx >= len(self._stages) - 1:
            return False
        stage = self.current_stage
        if self._stage_steps < stage.min_steps:
            return False
        if len(self._outcomes) < min(20, self._outcome_window):
            return False
        return self.win_rate >= stage.win_threshold

    def _advance_stage(self) -> None:
        old_name = self.current_stage.name
        old_wr = self.win_rate
        self._stage_idx += 1
        self._stage_steps = 0
        self._updates_in_stage = 0
        self._outcomes.clear()
        print(
            f"\n[curriculum] {old_name} → {self.current_stage.name}"
            f"  win_rate={old_wr:.2f}\n"
        )
        self._env = self._build_env()

    def _build_env(self) -> TribesEnv:
        stage = self.current_stage
        tribes = self._tribes_pool[: stage.n_tribes]

        if stage.opp_type == "random":
            return TribesEnv(
                tribes_enum=tribes, opponent_cls=RandomAgent, seed=self._seed
            )

        if stage.opp_type == "mixed":
            # Build with RandomAgent as default; reset() will swap per-episode.
            return TribesEnv(
                tribes_enum=tribes, opponent_cls=RandomAgent, seed=self._seed
            )

        if stage.opp_type == "simple":
            return TribesEnv(
                tribes_enum=tribes, opponent_cls=SimpleAgent, seed=self._seed
            )

        if stage.opp_type == "handicapped":
            # Build pre-constructed HandicappedAgent opponents so each gets its
            # own RNG and the handicap fraction is applied per-action.
            n_opps = stage.n_tribes - 1
            opp_agents = [
                HandicappedAgent(
                    SimpleAgent(self._seed + i), stage.handicap, self._seed + i + 1000
                )
                for i in range(n_opps)
            ]
            return TribesEnv(
                tribes_enum=tribes, opponent_agents=opp_agents, seed=self._seed
            )

        # Self-play: use frozen snapshot; fall back to RandomAgent until first sync
        if self._self_play_snapshot is None:
            return TribesEnv(
                tribes_enum=tribes, opponent_cls=RandomAgent, seed=self._seed
            )

        n_opps = stage.n_tribes - 1
        opp_agents = [
            SelfPlayAgent(self._seed + i, self._self_play_snapshot, stage.n_tribes)
            for i in range(n_opps)
        ]
        return TribesEnv(
            tribes_enum=tribes, opponent_agents=opp_agents, seed=self._seed
        )

    def _sync_self_play(self, policy) -> None:
        self._self_play_snapshot = copy.deepcopy(policy)
        if hasattr(self._self_play_snapshot, "set_training_mode"):
            self._self_play_snapshot.set_training_mode(False)
        # Rebuild env so opponents immediately use the updated snapshot
        if self.current_stage.opp_type == "self":
            self._env = self._build_env()
        print(
            f"[curriculum] Synced self-play snapshot  stage={self.current_stage.name}"
        )
