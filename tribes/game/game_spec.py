"""GameSpec — JSON-serialisable configuration for a single game.

Resolution order when fields are absent:
    tribes_cnt  →  tribes  →  players  →  level
"""

from __future__ import annotations

import json
import random as _random
import time
from dataclasses import dataclass
from typing import Optional

from tribes.types import GAME_MODE, TRIBE as TRIBE_TYPE


_TRIBE_NAME_MAP: dict[str, TRIBE_TYPE] = {
    "xin xi": TRIBE_TYPE.XIN_XI,
    "xin_xi": TRIBE_TYPE.XIN_XI,
    "imperius": TRIBE_TYPE.IMPERIUS,
    "bardur": TRIBE_TYPE.BARDUR,
    "oumaji": TRIBE_TYPE.OUMAJI,
    "kickoo": TRIBE_TYPE.KICKOO,
    "hoodrick": TRIBE_TYPE.HOODRICK,
    "luxidoor": TRIBE_TYPE.LUXIDOOR,
    "vengir": TRIBE_TYPE.VENGIR,
    "zebasi": TRIBE_TYPE.ZEBASI,
    "ai-mo": TRIBE_TYPE.AI_MO,
    "ai_mo": TRIBE_TYPE.AI_MO,
    "quetzali": TRIBE_TYPE.QUETZALI,
    "yadakk": TRIBE_TYPE.YADAKK,
}


def parse_tribe(name: str) -> TRIBE_TYPE:
    key = name.strip().lower()
    if key not in _TRIBE_NAME_MAP:
        raise ValueError(f"Unknown tribe: {name!r}")
    return _TRIBE_NAME_MAP[key]


def _count_tribes_in_lines(lines: list[str]) -> int:
    count = 0
    for line in lines:
        for token in line.split(","):
            parts = token.strip().split(":")
            if (
                parts[0]
                and parts[0][0] == "c"
                and len(parts) == 2
                and parts[1].isdigit()
            ):
                count += 1
    return count


@dataclass
class GameSpec:
    """All information needed to configure a single game.

    Any absent field is auto-filled during :meth:`resolve`.

    Fields
    ------
    tribes_cnt : int, optional
        Number of tribes.  Inferred from ``tribes`` or ``level`` if absent.
    tribes : list[str], optional
        Tribe names.  Randomly chosen if absent.
    players : list[str], optional
        Agent type per slot (``"random"``, ``"simple"``, ``"donothing"``).
        Defaults to all ``"random"``.
    level : str or list[str], optional
        CSV file path, inline CSV rows, or ``None`` to auto-generate.
    seed : int, optional
        RNG seed.  Time-based if absent.
    mode : str
        ``"capitals"`` (default) or ``"score"``.
    """

    tribes_cnt: Optional[int] = None
    tribes: Optional[list[str]] = None
    players: Optional[list[str]] = None
    level: Optional[list[str]] = None
    seed: Optional[int] = None
    mode: str = "capitals"

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: str) -> GameSpec:
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> GameSpec:
        return cls(
            tribes_cnt=data.get("tribes_cnt"),
            tribes=data.get("tribes"),
            players=data.get("players"),
            level=data.get("level"),
            seed=data.get("seed"),
            mode=data.get("mode", "capitals"),
        )

    def to_dict(self) -> dict:
        d: dict = {"mode": self.mode}
        if self.tribes_cnt is not None:
            d["tribes_cnt"] = self.tribes_cnt
        if self.tribes is not None:
            d["tribes"] = self.tribes
        if self.players is not None:
            d["players"] = self.players
        if self.level is not None:
            d["level"] = self.level
        if self.seed is not None:
            d["seed"] = self.seed
        return d

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(self, rng: Optional[_random.Random] = None) -> ResolvedSpec:
        """Return a :class:`ResolvedSpec` with every field filled in."""
        rng = rng or _random.Random()

        seed = (
            self.seed
            if self.seed is not None
            else int(time.time() * 1000) & 0xFFFF_FFFF
        )

        # tribes_cnt
        if self.tribes is not None:
            n = len(self.tribes)
        elif self.tribes_cnt is not None:
            n = self.tribes_cnt
        elif self.level is not None:
            n = _count_tribes_in_lines(self.level)
        else:
            n = 2

        # tribes
        if self.tribes is not None:
            tribes_enum = [parse_tribe(t) for t in self.tribes]
        else:
            all_tribes = list(TRIBE_TYPE)
            tribes_enum = rng.sample(all_tribes, k=min(n, len(all_tribes)))

        # players
        players = list(self.players) if self.players is not None else ["random"] * n
        if len(players) != n:
            raise ValueError(
                f"players length ({len(players)}) does not match" f" tribes count ({n})"
            )

        # game_mode
        game_mode = (
            GAME_MODE.CAPITALS if self.mode.lower() == "capitals" else GAME_MODE.SCORE
        )

        # level lines
        level_lines = list(self.level) if self.level is not None else None

        return ResolvedSpec(
            tribes_enum=tribes_enum,
            players=players,
            level_lines=level_lines,
            seed=seed,
            game_mode=game_mode,
        )


@dataclass
class ResolvedSpec:
    """Fully resolved game configuration — no optional fields."""

    tribes_enum: list[TRIBE_TYPE]
    players: list[str]
    level_lines: Optional[list[str]]  # None → procedural generation
    seed: int
    game_mode: GAME_MODE
