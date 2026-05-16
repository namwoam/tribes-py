# Tribes — Python Port

[![CI](https://github.com/GAIGResearch/Tribes/actions/workflows/ci.yml/badge.svg)](https://github.com/GAIGResearch/Tribes/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)

A Python port of [Tribes](https://github.com/GAIGResearch/Tribes) — a multi-player, turn-based strategy game framework designed for AI research. The game involves managing a technology tree, economy, and unit combat across a partially-observable hex-style grid.

## Requirements

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) (recommended) **or** pip

Optional:
- `pygame >= 2.6` for the graphical interface

## Installation

```bash
git clone <repo-url>
cd tribes-py
uv sync              # installs core + dev extras
# or: pip install -e ".[test,dev]"
```

## Running a game

```bash
# Headless game (random agents, auto-picks first level file)
uv run python main.py

# Specify a level and agents
uv run python main.py --level levels/sample_level.csv --players random --players simple

# Enable the pygame GUI
uv run python main.py --level levels/sample_level.csv --gui

# Score mode instead of Capitals
uv run python main.py --mode score --players random --players donothing --players random --players donothing

# Set a fixed seed
uv run python main.py --seed 42
```

### CLI reference

| Flag | Default | Description |
|---|---|---|
| `--level FILE` | auto-detect | Path to a CSV level file |
| `--players TYPE` | `random random` | Agent type per player slot; repeat for multiple players |
| `--mode capitals\|score` | `capitals` | Win condition |
| `--seed INT` | random | RNG seed for reproducibility |
| `--gui` | off | Open pygame window |
| `--verbose` | off | Print detailed game events |
| `--tournament JSON` | — | Run a tournament (see below) |

### Agent types

| Name | Description |
|---|---|
| `random` | Picks a uniformly random legal action each turn |
| `donothing` | Always ends the turn immediately |
| `simple` | Greedy heuristic agent (rule-based) |

## Running a tournament

```bash
uv run python main.py --tournament sample-config.json
```

Example `sample-config.json`:

```json
{
  "Game Mode": "Capitals",
  "Repetitions": 3,
  "Shift Tribes": true,
  "Verbose": false,
  "Players": ["random", "simple", "random", "simple"],
  "Tribes": ["Imperius", "Bardur", "Oumaji", "Xin Xi"],
  "Level Seeds": [42, 123]
}
```

Results are printed per player: win rate, mean score, technologies researched, cities, production, wars declared, and stars.

## Level files

Pre-built levels live in `levels/`. All files are CSV with terrain/unit/resource tokens:

| File | Players | Notes |
|---|---|---|
| `sample_level.csv` | 4 | Default 4-player map |
| `sample_level_2p.csv` | 2 | Small 2-player map |
| `balanced_level_4p.csv` | 4 | Symmetric 4-player map |
| `minimal_level.csv` | 2 | Tiny map for unit tests |

## Tribes

Twelve playable tribes, each with a unique starting technology and unit:
`Xin Xi`, `Imperius`, `Bardur`, `Oumaji`, `Kickoo`, `Hoodrick`,
`Luxidoor`, `Vengir`, `Zebasi`, `Ai-Mo`, `Quetzali`, `Yadakk`.

## Testing

```bash
uv run pytest tests/unit/   # fast unit tests
uv run pytest tests/e2e/    # full game runs
uv run pytest tests/ --cov=tribes   # with coverage
```

## Code quality

```bash
uv run flake8 tribes tests main.py   # lint

# Install pre-commit hooks (run once after cloning)
uv run pre-commit install
uv run pre-commit run --all-files
```

## Version bumping

PR branches must start with `major/`, `minor/`, or `patch/`. Merging one of these branches into `master` or `main` automatically bumps `pyproject.toml`, commits the new version, creates a GitHub Release, uploads the built distributions as release assets, and deletes the merged branch via GitHub Actions.

## Game modes

| Mode | Win condition |
|---|---|
| `Capitals` | Capture all enemy capitals (max 50 turns) |
| `Score` | Highest score after 30 turns |

## Associated research

Diego Perez Liebana, Yu-Jhen Hsu, Stavros Emmanouilidis, Bobby Khaleque, Raluca Gaina,
**"Tribes: A New Turn-Based Strategy Game for AI"**,
_Sixteenth AAAI Conference on Artificial Intelligence and Interactive Digital Entertainment (AIIDE)_, 2020.
