"Evaluate a trained MaskablePPO model against SimpleAgent and RandomAgent."

from __future__ import annotations

import random
import click
import numpy as np

from tribes.gym_env import TribesEnv, game_state_to_obs, MAX_ACTIONS
from tribes.players.agent import Agent
from tribes.players.simple_agent import SimpleAgent
from tribes.players.random_agent import RandomAgent
from tribes.types import TRIBE as TRIBE_TYPE, RESULT


class RLAgent(Agent):
    """Wraps a saved MaskablePPO model as an Agent for tournament play."""

    def __init__(self, model_path: str, seed: int = 0) -> None:
        super().__init__(seed)
        from sb3_contrib import MaskablePPO
        self._model = MaskablePPO.load(model_path)

    def act(self, gs):
        obs = game_state_to_obs(gs)
        obs_batched = {k: v[np.newaxis] for k, v in obs.items()}

        legal = gs.get_all_available_actions()
        if not legal:
            from tribes.actions.tribe_actions.end_turn import EndTurn
            return EndTurn(gs.get_active_tribe_id())

        mask = np.zeros(MAX_ACTIONS, dtype=bool)
        mask[: len(legal)] = True

        action, _ = self._model.predict(
            obs_batched,
            action_masks=mask[np.newaxis],
            deterministic=True,
        )
        return legal[min(int(action[0]), len(legal) - 1)]

    def copy(self) -> "RLAgent":
        raise NotImplementedError


def run_eval(model_path: str, opponent_cls, n_games: int, seed: int) -> dict:
    """Run n_games of RL agent (player 0) vs opponent_cls. Returns stats."""
    rng = random.Random(seed)

    wins = losses = draws = 0
    rl_scores = []
    opp_scores = []

    for game_i in range(n_games):
        game_seed = rng.randint(0, 2**31)
        env = TribesEnv(
            tribes_enum=[TRIBE_TYPE.IMPERIUS, TRIBE_TYPE.BARDUR],
            opponent_cls=opponent_cls,
            seed=game_seed,
        )

        # Load model fresh per-batch or reuse — reuse for speed
        from sb3_contrib import MaskablePPO
        from sb3_contrib.common.wrappers import ActionMasker
        model = MaskablePPO.load(model_path)

        obs, info = env.reset()
        terminated = False
        while not terminated:
            mask = env.action_masks()
            obs_batched = {k: v[np.newaxis] for k, v in obs.items()}
            action, _ = model.predict(
                obs_batched, action_masks=mask[np.newaxis], deterministic=True
            )
            obs, reward, terminated, truncated, info = env.step(int(action[0]))
            if truncated:
                break

        result = env._gs.get_tribe(0).get_winner()
        if result is RESULT.WIN:
            wins += 1
        elif result is RESULT.LOSS:
            losses += 1
        else:
            draws += 1

        rl_scores.append(env._gs.get_score(0))
        opp_scores.append(env._gs.get_score(1))

        print(
            f"  game {game_i+1:>3}/{n_games}  "
            f"result={'WIN' if result is RESULT.WIN else ('LOSS' if result is RESULT.LOSS else 'DRAW')}  "
            f"rl_score={env._gs.get_score(0)}  opp_score={env._gs.get_score(1)}"
        )

    return {
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_rate": wins / n_games,
        "mean_rl_score": float(np.mean(rl_scores)),
        "mean_opp_score": float(np.mean(opp_scores)),
    }


@click.command(context_settings={"show_default": True})
@click.option("--model", default="runs/model_curriculum", help="Path to saved model (no .zip).")
@click.option("--n-games", default=50, type=int, help="Games per opponent.")
@click.option("--seed", default=42, type=int)
def main(model: str, n_games: int, seed: int) -> None:
    """Evaluate RL agent vs SimpleAgent and RandomAgent."""

    for opp_name, opp_cls in [("SimpleAgent", SimpleAgent), ("RandomAgent", RandomAgent)]:
        print(f"\n=== RL vs {opp_name} ({n_games} games) ===")
        stats = run_eval(model, opp_cls, n_games, seed)
        print(
            f"\n  Win rate : {stats['win_rate']:.1%}  ({stats['wins']}W / {stats['losses']}L / {stats['draws']}D)"
            f"\n  RL score : {stats['mean_rl_score']:.1f}"
            f"\n  Opp score: {stats['mean_opp_score']:.1f}"
        )


if __name__ == "__main__":
    main()
