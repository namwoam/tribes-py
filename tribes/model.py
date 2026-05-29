"Custom feature extractor for TribesEnv's Dict observation space."

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from gymnasium import spaces
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

# Board constants (must match gym_env.py)
_MAX_BOARD = 24
_MAX_TRIBES = 8

# 16 spatial channels: terrain, resource, building, unit_type,
# 8× unit_tribe binary planes (one per relative player), unit_hp, unit_fresh,
# city_owner, is_road.
# Per-channel normalisation: (offset, scale) → (val + offset) / scale ∈ [0, 1].
_SPATIAL_NORM = [
    (0.0, 7.0),    # terrain         [0, 7]
    (1.0, 8.0),    # resource        [-1, 7]
    (1.0, 19.0),   # building        [-1, 18]
    (1.0, 12.0),   # unit_type       [-1, 11]
    # 8 binary planes: unit_tribe_0 (self) … unit_tribe_7 (7th opponent)
    (0.0, 1.0),    # unit_tribe_0    {0, 1}
    (0.0, 1.0),    # unit_tribe_1    {0, 1}
    (0.0, 1.0),    # unit_tribe_2    {0, 1}
    (0.0, 1.0),    # unit_tribe_3    {0, 1}
    (0.0, 1.0),    # unit_tribe_4    {0, 1}
    (0.0, 1.0),    # unit_tribe_5    {0, 1}
    (0.0, 1.0),    # unit_tribe_6    {0, 1}
    (0.0, 1.0),    # unit_tribe_7    {0, 1}
    (1.0, 11.0),   # unit_hp         [-1, 10]
    (1.0, 2.0),    # unit_fresh      [-1, 1]
    (1.0, 3.0),    # city_owner      [-1, 2]
    (0.0, 1.0),    # is_road         {0, 1}
]
_N_SPATIAL = len(_SPATIAL_NORM)  # 16

# Tribe-stat normalisers
_STARS_SCALE  = 100.0
_SCORE_SCALE  = 500.0
_CITIES_SCALE = float(_MAX_BOARD ** 2)
_KILLS_SCALE  = 50.0
_TECHS_SCALE  = 23.0


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

class _ResBlock(nn.Module):
    """Pre-activation residual block: BN → ReLU → Conv → BN → ReLU → Conv + skip."""

    def __init__(self, channels: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.BatchNorm2d(channels),
            nn.ReLU(),
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(),
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


# ---------------------------------------------------------------------------
# Feature extractor
# ---------------------------------------------------------------------------

class TribesFeatureExtractor(BaseFeaturesExtractor):
    """Residual spatial CNN + tribe-stats MLP feature extractor.

    Architecture
    ------------
    Spatial branch (16 board channels)
        Entry conv  16 → 64,  24×24
        ResBlock    64,       24×24
        MaxPool              → 12×12
        Conv        64 → 128, 12×12
        ResBlock    128,      12×12
        MaxPool              → 6×6
        Conv        128 → 256, 6×6
        ResBlock    256,       6×6
        Global-Avg-Pool + Global-Max-Pool → concat 512-dim

    Tribe-stats branch  (40 tribe scalars + 1 game_tick → 41 total)
        Linear(41 → 256) → ReLU → Linear(256 → 128) → ReLU  →  128-dim

    Head
        Linear(512 + 128 → features_dim) → ReLU
    """

    def __init__(
        self,
        observation_space: spaces.Dict,
        features_dim: int = 512,
    ) -> None:
        super().__init__(observation_space, features_dim)

        self.spatial_enc = nn.Sequential(
            # Entry: 16 → 64, keep 24×24
            nn.Conv2d(_N_SPATIAL, 64, 3, padding=1, bias=False),
            _ResBlock(64),
            nn.MaxPool2d(2),          # → 12×12
            # Stage 2: 64 → 128
            nn.Conv2d(64, 128, 3, padding=1, bias=False),
            _ResBlock(128),
            nn.MaxPool2d(2),          # → 6×6
            # Stage 3: 128 → 256
            nn.Conv2d(128, 256, 3, padding=1, bias=False),
            _ResBlock(256),
            # Final BN+ReLU to activate before pooling
            nn.BatchNorm2d(256),
            nn.ReLU(),
        )
        spatial_out = 256 * 2  # GAP(256) + GMP(256) = 512

        # 5 tribe-stat vectors × MAX_TRIBES dims + 1 game_tick scalar = 41
        tribe_in = _MAX_TRIBES * 5 + 1
        self.tribe_net = nn.Sequential(
            nn.Linear(tribe_in, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
        )

        self.head = nn.Sequential(
            nn.Linear(spatial_out + 128, features_dim),
            nn.ReLU(),
        )

        # Normalisation buffers (move to device automatically)
        offsets = torch.tensor([o for o, _ in _SPATIAL_NORM]).view(1, _N_SPATIAL, 1, 1)
        scales  = torch.tensor([s for _, s in _SPATIAL_NORM]).view(1, _N_SPATIAL, 1, 1)
        self.register_buffer("_sp_offsets", offsets)
        self.register_buffer("_sp_scales",  scales)

    def forward(self, obs: dict[str, torch.Tensor]) -> torch.Tensor:
        # --- Spatial branch ---
        spatial = torch.stack(
            [
                obs["terrain"],
                obs["resource"],
                obs["building"],
                obs["unit_type"],
                obs["unit_tribe_0"],
                obs["unit_tribe_1"],
                obs["unit_tribe_2"],
                obs["unit_tribe_3"],
                obs["unit_tribe_4"],
                obs["unit_tribe_5"],
                obs["unit_tribe_6"],
                obs["unit_tribe_7"],
                obs["unit_hp"],
                obs["unit_fresh"],
                obs["city_owner"],
                obs["is_road"],
            ],
            dim=1,
        ).float()
        spatial = (spatial + self._sp_offsets) / self._sp_scales  # → [0, 1]

        feat = self.spatial_enc(spatial)                          # (B, 256, 6, 6)
        gap  = F.adaptive_avg_pool2d(feat, 1).flatten(1)         # (B, 256)
        gmp  = F.adaptive_max_pool2d(feat, 1).flatten(1)         # (B, 256)
        spatial_out = torch.cat([gap, gmp], dim=1)               # (B, 512)

        # --- Tribe-stats + game_tick branch ---
        tribe_stats = torch.cat(
            [
                obs["tribe_stars"].float()  / _STARS_SCALE,
                obs["tribe_score"].float()  / _SCORE_SCALE,
                obs["tribe_cities"].float() / _CITIES_SCALE,
                obs["tribe_kills"].float()  / _KILLS_SCALE,
                obs["tribe_techs"].float()  / _TECHS_SCALE,
                obs["game_tick"].float(),
            ],
            dim=1,
        )
        tribe_out = self.tribe_net(tribe_stats)                   # (B, 128)

        return self.head(torch.cat([spatial_out, tribe_out], dim=1))
