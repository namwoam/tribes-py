"""Integration tests for the train.py SB3 training script."""

from __future__ import annotations

import os

from click.testing import CliRunner

import train


# Minimal hyperparams that complete quickly but still exercise the real code path.
_FAST_KWARGS = dict(
    seed=0,
    self_play_sync=1,
    total_steps=256,
    n_steps=128,
    n_epochs=1,
    batch_size=64,
    lr=3e-4,
    gamma=0.99,
    gae_lambda=0.95,
    clip_eps=0.2,
    entropy_coef=0.01,
    value_coef=0.5,
    max_grad_norm=0.5,
    save_interval=0,
    resume="",
    tensorboard_log="",
    progress_bar=False,
)


# ---------------------------------------------------------------------------
# Environment builders
# ---------------------------------------------------------------------------


def test_build_env_has_correct_spaces():
    env = train.build_env(seed=0)
    assert hasattr(env, "observation_space")
    assert hasattr(env, "action_space")
    obs, _ = env.reset()
    assert set(obs.keys()) == {
        "terrain",
        "resource",
        "building",
        "unit_type",
        "unit_tribe",
        "tribe_stars",
        "tribe_score",
        "tribe_cities",
        "tribe_kills",
        "tribe_techs",
    }
    env.close()


def test_build_curriculum_env_has_correct_spaces():
    env = train.build_curriculum_env(seed=0, self_play_sync=1)
    assert hasattr(env, "observation_space")
    assert hasattr(env, "action_space")
    obs, info = env.reset()
    assert "curriculum_stage" in info
    env.close()


# ---------------------------------------------------------------------------
# run_sb3 – flat (no curriculum)
# ---------------------------------------------------------------------------


def test_run_sb3_saves_model(tmp_path):
    save_path = str(tmp_path / "model")
    train.run_sb3(curriculum=False, save=save_path, **_FAST_KWARGS)
    assert os.path.exists(save_path + ".zip"), "SB3 model file was not created"


def test_run_sb3_model_can_be_resumed(tmp_path):
    save_path = str(tmp_path / "model")
    train.run_sb3(curriculum=False, save=save_path, **_FAST_KWARGS)

    resume_save = str(tmp_path / "resumed")
    train.run_sb3(
        curriculum=False,
        save=resume_save,
        **{**_FAST_KWARGS, "total_steps": 128, "resume": save_path + ".zip"},
    )
    assert os.path.exists(resume_save + ".zip")


# ---------------------------------------------------------------------------
# run_sb3 – curriculum
# ---------------------------------------------------------------------------


def test_run_sb3_curriculum_saves_model(tmp_path):
    save_path = str(tmp_path / "curriculum_model")
    train.run_sb3(curriculum=True, save=save_path, **_FAST_KWARGS)
    assert os.path.exists(save_path + ".zip")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_help():
    result = CliRunner().invoke(train.main, ["--help"])
    assert result.exit_code == 0
    assert "total-steps" in result.output


def test_cli_runs_end_to_end(tmp_path):
    save_path = str(tmp_path / "cli_model")
    result = CliRunner().invoke(
        train.main,
        [
            "--total-steps",
            "256",
            "--n-steps",
            "128",
            "--n-epochs",
            "1",
            "--batch-size",
            "64",
            "--save",
            save_path,
            "--seed",
            "1",
        ],
    )
    assert result.exit_code == 0, result.output
    assert os.path.exists(save_path + ".zip")


def test_cli_curriculum_flag(tmp_path):
    save_path = str(tmp_path / "cli_curriculum")
    result = CliRunner().invoke(
        train.main,
        [
            "--curriculum",
            "--total-steps",
            "256",
            "--n-steps",
            "128",
            "--n-epochs",
            "1",
            "--batch-size",
            "64",
            "--save",
            save_path,
            "--seed",
            "2",
        ],
    )
    assert result.exit_code == 0, result.output
    assert os.path.exists(save_path + ".zip")


def test_cli_resume(tmp_path):
    save_path = str(tmp_path / "base")
    CliRunner().invoke(
        train.main,
        [
            "--total-steps",
            "256",
            "--n-steps",
            "128",
            "--n-epochs",
            "1",
            "--batch-size",
            "64",
            "--save",
            save_path,
        ],
    )

    resumed_path = str(tmp_path / "resumed")
    result = CliRunner().invoke(
        train.main,
        [
            "--total-steps",
            "128",
            "--n-steps",
            "128",
            "--n-epochs",
            "1",
            "--batch-size",
            "64",
            "--save",
            resumed_path,
            "--resume",
            save_path + ".zip",
        ],
    )
    assert result.exit_code == 0, result.output
    assert os.path.exists(resumed_path + ".zip")
