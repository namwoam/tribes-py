"Gymnasium environment wrapping the Tribes game."

from __future__ import annotations

import random
from typing import Optional

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from tribes.game.game_state import GameState
from tribes.players.random_agent import RandomAgent
from tribes.types import ACTION, GAME_MODE, TERRAIN, TRIBE as TRIBE_TYPE, RESULT
from tribes.constants import MAX_TURNS

MAX_BOARD_SIZE = 24
MAX_N_TRIBES = 8
MAX_ACTIONS = 512

WIN_REWARD = 100.0
LOSS_REWARD = -100.0

# Shaped-reward bonuses for discrete game milestones.
# These fire the moment the event occurs, giving dense credit-assignment signal
# for the multi-step sequences that lead to city capture / tech unlock / kill.
_CITY_BONUS = 5.0    # per new city gained (village capture or conquest)
_TECH_BONUS = 2.0    # per technology researched
_KILL_BONUS = 1.0    # per enemy unit killed
# Divisor for raw score delta so it stays in a similar range as the bonuses.
_SCORE_NORM = 100.0


# ---------------------------------------------------------------------------
# Standalone observation encoder
# ---------------------------------------------------------------------------


def game_state_to_obs(gs, perspective: int = 0) -> dict:
    """Convert a live GameState to the TribesEnv Dict observation format.

    Can be called outside TribesEnv (e.g. by SelfPlayAgent) as long as the
    GameState has been initialised and compute_player_actions has been called.

    Parameters
    ----------
    perspective:
        Tribe ID of the agent whose point-of-view we encode.  Units belonging
        to this tribe are encoded as +1 in ``unit_tribe``; all other units are
        encoded as -1.  The default (0) is correct for the main RL agent.
    """
    board = gs.get_board()
    size = board.get_size()
    capped = min(size, MAX_BOARD_SIZE)
    n_players = min(len(gs.get_tribes()), MAX_N_TRIBES)

    fog_key = TERRAIN.FOG.get_key()
    terrain    = np.full((MAX_BOARD_SIZE, MAX_BOARD_SIZE), fog_key, dtype=np.int8)
    resource   = np.full((MAX_BOARD_SIZE, MAX_BOARD_SIZE), -1, dtype=np.int8)
    building   = np.full((MAX_BOARD_SIZE, MAX_BOARD_SIZE), -1, dtype=np.int8)
    unit_type  = np.full((MAX_BOARD_SIZE, MAX_BOARD_SIZE), -1, dtype=np.int8)
    unit_tribe = np.full((MAX_BOARD_SIZE, MAX_BOARD_SIZE), -1, dtype=np.int8)
    # New channels
    unit_hp    = np.full((MAX_BOARD_SIZE, MAX_BOARD_SIZE), -1, dtype=np.int8)
    unit_fresh = np.full((MAX_BOARD_SIZE, MAX_BOARD_SIZE), -1, dtype=np.int8)
    city_owner = np.full((MAX_BOARD_SIZE, MAX_BOARD_SIZE), -1, dtype=np.int8)
    is_road    = np.zeros((MAX_BOARD_SIZE, MAX_BOARD_SIZE), dtype=np.int8)

    for x in range(capped):
        for y in range(capped):
            t = board.get_terrain_at(x, y)
            if t is not None:
                terrain[x, y] = t.get_key()
            r = board.get_resource_at(x, y)
            if r is not None:
                resource[x, y] = r.get_key()
            b = board.get_building_at(x, y)
            if b is not None:
                building[x, y] = b.get_key()
            unit = board.get_unit_at(x, y)
            if unit is not None:
                unit_type[x, y] = unit.get_type().get_key()
                # Encode relative player index: 0=self, 1=next opponent, 2=opponent after, …
                # so the agent can distinguish which enemy is which in multi-player games.
                unit_tribe[x, y] = (unit.tribe_id - perspective) % n_players
                max_hp = unit.get_max_hp()
                unit_hp[x, y] = round(10 * unit.get_current_hp() / max_hp) if max_hp > 0 else 0
                unit_fresh[x, y] = 1 if unit.is_fresh() else 0
            city = board.get_city_in_borders(x, y)
            if city is not None:
                if city.tribe_id == -1:
                    city_owner[x, y] = 0   # neutral/uncaptured village
                elif city.tribe_id == perspective:
                    city_owner[x, y] = 1   # own city
                else:
                    city_owner[x, y] = 2   # enemy city
            if board.is_road(x, y):
                is_road[x, y] = 1

    tribe_stars = np.zeros(MAX_N_TRIBES, dtype=np.int32)
    tribe_score = np.zeros(MAX_N_TRIBES, dtype=np.int32)
    tribe_cities = np.zeros(MAX_N_TRIBES, dtype=np.int32)
    tribe_kills = np.zeros(MAX_N_TRIBES, dtype=np.int32)
    tribe_techs = np.zeros(MAX_N_TRIBES, dtype=np.int32)

    for i in range(n_players):
        t = gs.get_tribe(i)
        tribe_stars[i] = t.get_stars()
        tribe_score[i] = t.get_score()
        tribe_cities[i] = t.get_num_cities()
        tribe_kills[i] = t.get_n_kills()
        tribe_techs[i] = t.get_tech_tree().get_num_researched()

    game_tick = np.array([gs.get_tick() / MAX_TURNS], dtype=np.float32)

    return {
        "terrain": terrain,
        "resource": resource,
        "building": building,
        "unit_type": unit_type,
        "unit_tribe": unit_tribe,
        "unit_hp": unit_hp,
        "unit_fresh": unit_fresh,
        "city_owner": city_owner,
        "is_road": is_road,
        "tribe_stars": tribe_stars,
        "tribe_score": tribe_score,
        "tribe_cities": tribe_cities,
        "tribe_kills": tribe_kills,
        "tribe_techs": tribe_techs,
        "game_tick": game_tick,
    }


class TribesEnv(gym.Env):
    """Single-agent Gymnasium wrapper for the Tribes strategy game.

    Player 0 is the controlled agent; all other players are driven by
    `opponent_cls` (default: RandomAgent).  Each call to `step()` executes
    exactly one action for player 0.  Opponent turns run automatically after
    player 0 ends their turn.

    Observation space (Dict):
        terrain      (MAX_BOARD_SIZE, MAX_BOARD_SIZE) int8  TERRAIN.key; 7=fog
        resource     (MAX_BOARD_SIZE, MAX_BOARD_SIZE) int8  RESOURCE.key; -1=none
        building     (MAX_BOARD_SIZE, MAX_BOARD_SIZE) int8  BUILDING.key; -1=none
        unit_type    (MAX_BOARD_SIZE, MAX_BOARD_SIZE) int8  UNIT.key; -1=none
        unit_tribe   (MAX_BOARD_SIZE, MAX_BOARD_SIZE) int8  tribe_id; -1=none
        tribe_stars  (MAX_N_TRIBES,) int32
        tribe_score  (MAX_N_TRIBES,) int32
        tribe_cities (MAX_N_TRIBES,) int32
        tribe_kills  (MAX_N_TRIBES,) int32
        tribe_techs  (MAX_N_TRIBES,) int32

    Action space:
        Discrete(MAX_ACTIONS).  `info["action_mask"]` is a bool array marking
        the valid indices; agents should only choose indices where mask is True.
    """

    metadata: dict = {"render_modes": []}

    def __init__(
        self,
        level_file: Optional[str] = None,
        tribes_enum: Optional[list] = None,
        game_mode: GAME_MODE = GAME_MODE.SCORE,
        seed: int = 0,
        opponent_cls=None,
        opponent_agents: Optional[list] = None,
        render_mode: Optional[str] = None,
    ) -> None:
        super().__init__()

        self._level_file = level_file
        self._tribes_enum = tribes_enum
        self._game_mode = game_mode
        self._init_seed = seed
        self._opponent_cls = opponent_cls or RandomAgent
        self._opponent_agents = opponent_agents  # pre-built opponents (overrides cls)
        self.render_mode = render_mode

        board_shape = (MAX_BOARD_SIZE, MAX_BOARD_SIZE)
        self.observation_space = spaces.Dict(
            {
                "terrain": spaces.Box(0, 7, board_shape, dtype=np.int8),
                "resource": spaces.Box(-1, 7, board_shape, dtype=np.int8),
                "building": spaces.Box(-1, 18, board_shape, dtype=np.int8),
                "unit_type": spaces.Box(-1, 11, board_shape, dtype=np.int8),
                "unit_tribe": spaces.Box(-1, MAX_N_TRIBES - 1, board_shape, dtype=np.int8),
                "tribe_stars": spaces.Box(0, 2**15, (MAX_N_TRIBES,), dtype=np.int32),
                "tribe_score": spaces.Box(0, 2**15, (MAX_N_TRIBES,), dtype=np.int32),
                "tribe_cities": spaces.Box(
                    0, MAX_BOARD_SIZE**2, (MAX_N_TRIBES,), dtype=np.int32
                ),
                "tribe_kills": spaces.Box(0, 2**15, (MAX_N_TRIBES,), dtype=np.int32),
                "tribe_techs": spaces.Box(0, 23, (MAX_N_TRIBES,), dtype=np.int32),
                "game_tick": spaces.Box(0.0, 1.0, (1,), dtype=np.float32),
                "unit_hp": spaces.Box(-1, 10, board_shape, dtype=np.int8),
                "unit_fresh": spaces.Box(-1, 1, board_shape, dtype=np.int8),
                "city_owner": spaces.Box(-1, 2, board_shape, dtype=np.int8),
                "is_road": spaces.Box(0, 1, board_shape, dtype=np.int8),
            }
        )
        self.action_space = spaces.Discrete(MAX_ACTIONS)

        self._gs: Optional[GameState] = None
        self._opponents: list = []
        self._n_players: int = 0
        self._legal_actions: list = []
        self._prev_score: int = 0
        self._prev_cities: int = 0
        self._prev_techs: int = 0
        self._prev_kills: int = 0
        self._prev_relative_score: float = 0.0
        self._rng: random.Random = random.Random(seed)

    # ------------------------------------------------------------------
    # Gymnasium API
    # ------------------------------------------------------------------

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)

        if seed is not None:
            self._rng = random.Random(seed)

        tribes_enum = self._tribes_enum or [TRIBE_TYPE.IMPERIUS, TRIBE_TYPE.BARDUR]
        self._n_players = len(tribes_enum)

        game_seed = self._rng.randint(0, 2**31)
        level_seed = self._rng.randint(0, 2**31)

        rnd = random.Random(game_seed)
        self._gs = GameState(rnd, self._game_mode)

        if self._level_file is not None:
            self._gs.init(self._level_file)
        else:
            self._gs.init_generated(level_seed, tribes_enum)

        if self._opponent_agents is not None:
            self._opponents = list(self._opponent_agents)
        else:
            self._opponents = [
                self._opponent_cls(self._rng.randint(0, 2**31))
                for _ in range(self._n_players - 1)
            ]
        for i, opp in enumerate(self._opponents):
            opp.set_player_ids(i + 1, list(range(self._n_players)))

        self._init_player0_turn()
        tribe0 = self._gs.get_tribe(0)
        self._prev_score = self._gs.get_score(0)
        self._prev_cities = tribe0.get_num_cities()
        self._prev_techs = tribe0.get_tech_tree().get_num_researched()
        self._prev_kills = tribe0.get_n_kills()
        best_opp = (
            max(self._gs.get_score(i) for i in range(1, self._n_players))
        ) if self._n_players > 1 else 0.0
        self._prev_relative_score = float(self._prev_score) - best_opp

        return self._get_obs(), {"action_mask": self._get_action_mask()}

    def step(self, action_idx: int):
        assert self._gs is not None, "Call reset() before step()"

        tribe0 = self._gs.get_tribe(0)

        legal = self._legal_actions
        idx = min(int(action_idx), len(legal) - 1)
        action = legal[idx]

        self._gs.next(action)
        self._gs.compute_player_actions(tribe0)

        is_end_turn = action.action_type is ACTION.END_TURN
        has_more = self._gs.exist_available_actions(tribe0)

        if is_end_turn or not has_more:
            if not is_end_turn:
                from tribes.actions.tribe_actions.end_turn import EndTurn

                self._gs.next(EndTurn(self._gs.get_active_tribe_id()))
            self._gs.end_turn(tribe0)
            self._gs.game_over()

            if not self._gs.is_game_over():
                self._run_opponents()

            if not self._gs.is_game_over():
                self._gs.inc_tick()
                self._init_player0_turn()
        else:
            self._update_legal_actions()

        score = self._gs.get_score(0)
        cities = tribe0.get_num_cities()
        techs = tribe0.get_tech_tree().get_num_researched()
        kills = tribe0.get_n_kills()

        best_opp = (
            max(self._gs.get_score(i) for i in range(1, self._n_players))
        ) if self._n_players > 1 else 0.0
        relative_score = float(score) - best_opp

        reward = (
            (relative_score - self._prev_relative_score) / _SCORE_NORM
            + _CITY_BONUS * (cities - self._prev_cities)
            + _TECH_BONUS * (techs - self._prev_techs)
            + _KILL_BONUS * (kills - self._prev_kills)
        )

        self._prev_score = score
        self._prev_cities = cities
        self._prev_techs = techs
        self._prev_kills = kills
        self._prev_relative_score = relative_score

        terminated = self._gs.is_game_over()

        if terminated:
            result = tribe0.get_winner()
            if result is RESULT.WIN:
                reward += WIN_REWARD
            elif result is RESULT.LOSS:
                # Scale penalty by placement: last place gets full -100, higher
                # placements get a proportionally smaller penalty so the agent
                # learns that staying competitive in multi-player games matters.
                final_score = self._gs.get_score(0)
                n_ahead = sum(
                    1 for i in range(1, self._n_players)
                    if self._gs.get_score(i) > final_score
                )
                loss_scale = n_ahead / max(self._n_players - 1, 1)
                reward += LOSS_REWARD * loss_scale

        obs = self._get_obs()
        info = {"action_mask": self._get_action_mask()}
        if terminated:
            info["is_win"] = result is RESULT.WIN
            info["is_loss"] = result is RESULT.LOSS
        return obs, reward, terminated, False, info

    def action_masks(self) -> np.ndarray:
        """Return a bool mask of valid action indices (for MaskablePPO)."""
        return self._get_action_mask()

    def render(self):
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_player0_turn(self) -> None:
        tribe0 = self._gs.get_tribe(0)
        if tribe0.get_winner() is not RESULT.INCOMPLETE:
            return
        self._gs.init_turn(tribe0)
        self._gs.compute_player_actions(tribe0)
        self._update_legal_actions()

    def _update_legal_actions(self) -> None:
        self._legal_actions = self._gs.get_all_available_actions()
        if not self._legal_actions:
            from tribes.actions.tribe_actions.end_turn import EndTurn

            self._legal_actions = [EndTurn(self._gs.get_active_tribe_id())]

    def _get_action_mask(self) -> np.ndarray:
        mask = np.zeros(MAX_ACTIONS, dtype=bool)
        mask[: len(self._legal_actions)] = True
        return mask

    def _run_opponents(self) -> None:
        tribes = self._gs.get_tribes()
        for i in range(1, self._n_players):
            tribe = tribes[i]
            if tribe.get_winner() is not RESULT.INCOMPLETE:
                continue
            self._run_single_opponent(i, tribe)
            if self._gs.is_game_over():
                return

    def _run_single_opponent(self, player_id: int, tribe) -> None:
        from tribes.actions.tribe_actions.end_turn import EndTurn

        self._gs.init_turn(tribe)
        self._gs.compute_player_actions(tribe)
        obs = self._gs.copy(-1)

        agent = self._opponents[player_id - 1]
        continue_turn = True

        while True:
            action = None
            if continue_turn:
                action = agent.act(obs)
                continue_turn = (
                    not self._gs.is_turn_ending()
                    and self._gs.exist_available_actions(tribe)
                )

            if action is None and not continue_turn:
                action = EndTurn(self._gs.get_active_tribe_id())

            if action is not None:
                self._gs.next(action)
                self._gs.compute_player_actions(tribe)
                obs = self._gs.copy(-1)

            if action is not None and action.action_type is ACTION.END_TURN:
                break
            if self._gs.game_over():
                break

        self._gs.end_turn(tribe)

    def _get_obs(self) -> dict:
        return game_state_to_obs(self._gs)
