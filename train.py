"Model-agnostic training harness for TribesEnv (primary: SB3 MaskablePPO)."

from __future__ import annotations

import os

import click
import numpy as np
import torch

# ---------------------------------------------------------------------------
# Build helpers
# ---------------------------------------------------------------------------


def build_env(seed: int):
    from tribes.gym_env import TribesEnv

    return TribesEnv(seed=seed)


def build_curriculum_env(seed: int, self_play_sync: int):
    from tribes.curriculum import CurriculumEnv

    return CurriculumEnv(seed=seed, self_play_sync_interval=self_play_sync)


# ---------------------------------------------------------------------------
# SB3 training path  (MaskablePPO)
# ---------------------------------------------------------------------------


def run_sb3(
    *,
    curriculum: bool,
    seed: int,
    self_play_sync: int,
    total_steps: int,
    n_steps: int,
    n_epochs: int,
    batch_size: int,
    lr: float,
    gamma: float,
    gae_lambda: float,
    clip_eps: float,
    entropy_coef: float,
    value_coef: float,
    max_grad_norm: float,
    save: str,
    save_interval: int,
    resume: str,
    tensorboard_log: str,
    progress_bar: bool,
) -> None:
    from sb3_contrib import MaskablePPO
    from sb3_contrib.common.wrappers import ActionMasker
    from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback

    env = build_curriculum_env(seed, self_play_sync) if curriculum else build_env(seed)
    masked_env = ActionMasker(env, lambda e: e.action_masks())

    tb_log = tensorboard_log or None

    if resume:
        model = MaskablePPO.load(resume, env=masked_env, tensorboard_log=tb_log)
        click.echo(f"Resumed from {resume}")
    else:
        model = MaskablePPO(
            policy="MultiInputPolicy",
            env=masked_env,
            learning_rate=lr,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            gamma=gamma,
            gae_lambda=gae_lambda,
            clip_range=clip_eps,
            ent_coef=entropy_coef,
            vf_coef=value_coef,
            max_grad_norm=max_grad_norm,
            verbose=0,
            seed=seed,
            tensorboard_log=tb_log,
        )

    # ---- Unified metrics + curriculum callback --------------------------------

    class _TrainCallback(BaseCallback):
        """Logs per-episode stats and drives curriculum self-play sync."""

        def __init__(self, curriculum_env=None, verbose=0):
            super().__init__(verbose)
            self._cenv = curriculum_env
            self._updates = 0
            # per-rollout accumulators
            self._ep_rewards: list[float] = []
            self._ep_lengths: list[int] = []
            self._ep_wins: list[float] = []
            self._cur_reward = 0.0
            self._cur_len = 0

        def _on_step(self) -> bool:
            self._cur_reward += float(self.locals["rewards"][0])
            self._cur_len += 1
            if self.locals["dones"][0]:
                info = self.locals["infos"][0]
                self._ep_rewards.append(self._cur_reward)
                self._ep_lengths.append(self._cur_len)
                self._ep_wins.append(float(info.get("is_win", False)))
                self._cur_reward = 0.0
                self._cur_len = 0
            return True

        def _on_rollout_end(self) -> bool:
            if self._ep_rewards:
                self.logger.record("ep/mean_reward", np.mean(self._ep_rewards))
                self.logger.record("ep/mean_length", np.mean(self._ep_lengths))
                self.logger.record("ep/win_rate", np.mean(self._ep_wins))
                n_ep = len(self._ep_rewards)
                self._ep_rewards.clear()
                self._ep_lengths.clear()
                self._ep_wins.clear()

                click.echo(
                    f"  step={self.num_timesteps:>9,}  "
                    f"ep={n_ep}  "
                    f"win={self.logger.name_to_value.get('ep/win_rate', 0):.2%}  "
                    f"rew={self.logger.name_to_value.get('ep/mean_reward', 0):+.2f}  "
                    f"len={self.logger.name_to_value.get('ep/mean_length', 0):.0f}"
                    + (f"  stage={self._cenv.current_stage.name}" if self._cenv else "")
                )

            if self._cenv is not None:
                self._updates += 1
                self.logger.record("curriculum/stage_idx", self._cenv._stage_idx)
                self.logger.record("curriculum/stage_win_rate", self._cenv.win_rate)
                self.logger.record("curriculum/stage_steps", self._cenv._stage_steps)
                self._cenv.notify_update(
                    policy=self.model.policy,
                    update_num=self._updates,
                )
            return True

    callbacks: list[BaseCallback] = [_TrainCallback(env if curriculum else None)]

    if save_interval:
        base, _ = os.path.splitext(save)
        callbacks.append(
            CheckpointCallback(
                save_freq=save_interval * n_steps,
                save_path=os.path.dirname(os.path.abspath(save)) or ".",
                name_prefix=os.path.basename(base),
            )
        )

    os.makedirs(os.path.dirname(os.path.abspath(save)) or ".", exist_ok=True)

    click.echo(
        f"\n[sb3-ppo] device={model.device}  curriculum={curriculum}  "
        f"total_steps={total_steps:,}  n_steps={n_steps}  batch={batch_size}  "
        f"lr={lr}  epochs={n_epochs}"
        + (f"\n[sb3-ppo] TensorBoard → {tb_log}" if tb_log else "")
    )

    model.learn(
        total_timesteps=total_steps,
        callback=callbacks,
        progress_bar=progress_bar,
        tb_log_name=os.path.basename(os.path.splitext(save)[0]),
    )
    model.save(save)
    click.echo(f"\nSaved → {save}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command(context_settings={"show_default": True})
# Mode
@click.option(
    "--curriculum",
    is_flag=True,
    help="Enable curriculum learning (random→simple→self-play, 2→4 tribes).",
)
# Environment
@click.option("--seed", default=0, type=int)
# Training schedule
@click.option("--total-steps", default=500_000, type=int, help="Total env steps.")
@click.option("--n-steps", default=2048, type=int, help="Rollout length.")
@click.option(
    "--save", default="runs/model", type=str, help="Output path (no ext for SB3)."
)
@click.option(
    "--save-interval", default=0, type=int, help="Checkpoint every N updates (0=off)."
)
@click.option("--resume", default="", type=str, help="Path to checkpoint to resume.")
@click.option(
    "--self-play-sync",
    default=20,
    type=int,
    help="Sync self-play snapshot every N gradient updates.",
)
# Hyper-parameters
@click.option("--lr", default=3e-4, type=float, help="Learning rate.")
@click.option("--n-epochs", default=10, type=int, help="Gradient epochs per rollout.")
@click.option("--batch-size", default=64, type=int)
@click.option("--gamma", default=0.99, type=float, help="Discount factor.")
@click.option("--gae-lambda", default=0.95, type=float)
@click.option("--clip-eps", default=0.2, type=float, help="PPO clip range.")
@click.option("--value-coef", default=0.5, type=float)
@click.option("--entropy-coef", default=0.03, type=float)
@click.option("--max-grad-norm", default=0.5, type=float)
# Logging / visualisation
@click.option(
    "--tensorboard-log",
    default="runs/tb",
    type=str,
    show_default=True,
    help="TensorBoard log directory (empty string to disable).",
)
@click.option("--progress-bar", is_flag=True, help="Show tqdm progress bar.")
def main(
    curriculum,
    seed,
    total_steps,
    n_steps,
    save,
    save_interval,
    resume,
    self_play_sync,
    lr,
    n_epochs,
    batch_size,
    gamma,
    gae_lambda,
    clip_eps,
    value_coef,
    entropy_coef,
    max_grad_norm,
    tensorboard_log,
    progress_bar,
):
    """Train a TribesEnv agent with SB3 MaskablePPO.

    Add --curriculum to enable the three-phase curriculum
    (random → simple → self-play, 2 → 4 tribes).
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    run_sb3(
        curriculum=curriculum,
        seed=seed,
        self_play_sync=self_play_sync,
        total_steps=total_steps,
        n_steps=n_steps,
        n_epochs=n_epochs,
        batch_size=batch_size,
        lr=lr,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_eps=clip_eps,
        entropy_coef=entropy_coef,
        value_coef=value_coef,
        max_grad_norm=max_grad_norm,
        save=save,
        save_interval=save_interval,
        resume=resume,
        tensorboard_log=tensorboard_log,
        progress_bar=progress_bar,
    )


if __name__ == "__main__":
    main()
