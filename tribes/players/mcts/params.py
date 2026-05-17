"Hyperparameters for the MCTS agent."

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class MCTSParams:
    # UCT exploration constant (sqrt(2) is the standard theoretical value).
    K: float = math.sqrt(2)
    # Maximum number of individual action steps to simulate per rollout.
    ROLLOUT_DEPTH: int = 20
    # Wall-clock budget per decision (milliseconds).
    TIME_BUDGET_MS: float = 100.0
    # Hard cap on MCTS iterations regardless of time.
    MAX_ITERATIONS: int = 500
    # Filter Destroy/Disband actions from the root action set.
    PRIORITIZE_ROOT: bool = True
