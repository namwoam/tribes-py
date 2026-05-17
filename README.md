# tribes-py

[![CI](https://github.com/namwoam/tribes-py/actions/workflows/ci.yml/badge.svg)](https://github.com/namwoam/tribes-py/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)

A Python port of [Tribes](https://github.com/GAIGResearch/Tribes) — a multi-player, turn-based strategy game framework designed for AI research. The game involves managing a technology tree, economy, and unit combat across a partially-observable hex-style grid.

## Requirements

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) (recommended) **or** pip

Optional:
- `pygame >= 2.6` for the graphical interface

## Installation

```bash
git clone https://github.com/namwoam/tribes-py
cd tribes-py
uv sync              # installs core + dev extras
# or: pip install -e ".[test,dev]"
```

## Running a game

```bash
# Headless game — auto-generated 2-player map, random agents
uv run python main.py

# Load a game-spec JSON file
uv run python main.py --level levels/sample_2p.json

# Override seed or mode from the command line
uv run python main.py --level levels/sample_4p.json --seed 42 --mode score

# Enable the pygame GUI
uv run python main.py --level levels/sample_2p.json --gui
```

### Game-spec JSON format

A game-spec JSON file captures everything needed to run a single game.
Fields are optional and are auto-filled in the following order:
`tribes_cnt` → `tribes` → `players` → `level`.

```json
{
  "tribes_cnt": 2,
  "tribes": ["bardur", "imperius"],
  "players": ["random", "simple"],
  "level": ["d:,d:,c:0,...", "d:,c:1,..."],
  "seed": 42,
  "mode": "capitals"
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `tribes_cnt` | int | inferred | Number of tribes; inferred from `tribes` or `level` |
| `tribes` | list[str] | random | Tribe name per slot |
| `players` | list[str] | all `"random"` | Agent type per slot |
| `level` | list[str] | auto-generate | Inline CSV rows (one string per map row); omit to procedurally generate |
| `seed` | int | random | RNG seed |
| `mode` | str | `"capitals"` | Win condition: `"capitals"` or `"score"` |

If `level` is omitted the board is procedurally generated from the resolved `tribes`.
If both `tribes` and `level` are omitted, two random tribes are chosen and the board is generated.

### CLI reference

| Flag | Default | Description |
|---|---|---|
| `--level JSON` | — | Path to a game-spec JSON file; omit to auto-generate |
| `--seed INT` | from spec | RNG seed (overrides spec value) |
| `--mode capitals\|score` | from spec | Win condition (overrides spec value) |
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
  "mode": "capitals",
  "repetitions": 3,
  "shift_tribes": true,
  "verbose": false,
  "players": ["random", "simple", "random", "simple"],
  "tribes": ["imperius", "bardur", "oumaji", "xin_xi"],
  "level_seeds": [42, 123]
}
```

Results are printed per player: win rate, mean score, technologies researched, cities, production, wars declared, and stars.

## Level files

Game-spec JSON files live in `levels/`. Each file is self-contained — the map grid is embedded as inline CSV rows inside the `"level"` field.

| File | Players | Notes |
|---|---|---|
| `sample_2p.json` | 2 | Small 2-player hand-crafted map |
| `sample_4p.json` | 4 | Default 4-player hand-crafted map |
| `sample_8p.json` | 8 | Large 8-player hand-crafted map (40×40) |
| `sample_4p_generated.json` | 4 | 4-player procedurally generated map |

## Tribes

Twelve playable tribes, each with a unique starting technology and unit:
`Xin Xi`, `Imperius`, `Bardur`, `Oumaji`, `Kickoo`, `Hoodrick`,
`Luxidoor`, `Vengir`, `Zebasi`, `Ai-Mo`, `Quetzali`, `Yadakk`.

## Testing

```bash
task test-unit   # fast unit tests
task test-e2e    # full game runs
task test        # all tests with coverage
```

## Code quality

```bash
task lint   # run all pre-commit hooks

# Install pre-commit hooks (run once after cloning)
uv run pre-commit install
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
