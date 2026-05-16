"Pygame-based GUI for Tribes-py, replacing the Java Swing GUI."
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

logger = logging.getLogger(__name__)

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False
    logger.warning("pygame not installed – GUI unavailable.")

if TYPE_CHECKING:
    from tribes.game.game import Game
    from tribes.game.game_state import GameState
    from tribes.actions.action import Action

# ---------------------------------------------------------------------------
# Terrain / BUILDING / UNIT colour fallbacks (used when no image available)
# ---------------------------------------------------------------------------

from tribes.types import TERRAIN, RESULT

_TERRAIN_COLORS: dict[TERRAIN, tuple[int, int, int]] = {
    TERRAIN.PLAIN:         (200, 210, 150),
    TERRAIN.SHALLOW_WATER: (100, 180, 240),
    TERRAIN.DEEP_WATER:    (30,  90, 180),
    TERRAIN.MOUNTAIN:      (140, 120,  90),
    TERRAIN.VILLAGE:       (230, 200, 120),
    TERRAIN.CITY:          (210, 140,  60),
    TERRAIN.FOREST:        ( 60, 140,  60),
    TERRAIN.FOG:           ( 80,  80,  80),
}

_RESULT_LABEL: dict[RESULT, str] = {
    RESULT.WIN:        "WIN",
    RESULT.LOSS:       "LOSS",
    RESULT.INCOMPLETE: "",
}

# ---------------------------------------------------------------------------
# Asset loader (caches images, falls back to colour-filled surfaces)
# ---------------------------------------------------------------------------

_IMG_CACHE: dict[str, "pygame.Surface"] = {}
_ASSET_ROOT = Path(__file__).parent.parent.parent  # repo root


def _load_image(rel_path: str, size: tuple[int, int]) -> "pygame.Surface":
    key = f"{rel_path}@{size}"
    if key in _IMG_CACHE:
        return _IMG_CACHE[key]
    full = _ASSET_ROOT / rel_path
    if full.exists():
        try:
            surf = pygame.image.load(str(full)).convert_alpha()
            surf = pygame.transform.scale(surf, size)
            _IMG_CACHE[key] = surf
            return surf
        except Exception:
            pass
    # Fallback: return None so caller can draw a colour rect
    _IMG_CACHE[key] = None  # type: ignore[assignment]
    return None  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

_CELL = 40           # pixels per tile
_SIDE_W = 260        # side-panel width
_INFO_H = 160        # bottom info-bar height
_FPS = 30


class GUI:
    """Top-down pygame rendering of a Tribes game."""

    def __init__(self, game: Game, title: str = "Tribes") -> None:
        if not _HAS_PYGAME:
            raise RuntimeError("pygame is required for the GUI.")

        pygame.init()
        pygame.display.set_caption(title)

        self._game = game
        self._closed = False
        self._gs: Optional[GameState] = None
        self._last_action: Optional[Action] = None

        # Compute window size from board dimensions
        board = game.get_board()
        self._grid = board.get_size()
        board_px = self._grid * _CELL
        w = board_px + _SIDE_W
        h = board_px + _INFO_H
        self._board_px = board_px

        self._screen = pygame.display.set_mode((w, h))
        self._clock = pygame.time.Clock()

        self._font_lg = pygame.font.SysFont("monospace", 14, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 11)

        # Pre-load terrain images
        self._terrain_imgs: dict[TERRAIN, Optional[pygame.Surface]] = {}
        for t in TERRAIN:
            self._terrain_imgs[t] = _load_image(t._image_file, (_CELL, _CELL))

        # Unit image folder mapping (unit type name → folder relative to img/unit/)
        self._unit_img_cache: dict[str, Optional[pygame.Surface]] = {}

    # ------------------------------------------------------------------
    # Public interface expected by Game.run()
    # ------------------------------------------------------------------

    def update(self, gs: GameState, action: Optional[Action]) -> None:
        self._gs = gs
        self._last_action = action
        self._render()
        self._clock.tick(_FPS)

    def pump(self) -> None:
        """Process pending events; call when game is over to keep window alive."""
        self._handle_events()

    def is_closed(self) -> bool:
        self._handle_events()
        return self._closed

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._closed = True
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    self._closed = True

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self) -> None:
        if self._gs is None:
            return
        self._handle_events()
        if self._closed:
            return

        self._screen.fill((20, 20, 20))
        self._draw_board()
        self._draw_side_panel()
        self._draw_info_bar()
        pygame.display.flip()

    def _draw_board(self) -> None:
        gs = self._gs
        board = gs.get_board()
        size = board.get_size()
        tribes = gs.get_tribes()

        # Build a quick tribe-id → color map
        tribe_colors: dict[int, tuple[int, int, int]] = {}
        for tribe in tribes:
            tribe_colors[tribe.tribe_id] = tribe.get_type().get_color()

        for x in range(size):
            for y in range(size):
                px = x * _CELL
                py = y * _CELL
                rect = pygame.Rect(px, py, _CELL, _CELL)

                terrain = board.get_terrain_at(x, y)
                img = self._terrain_imgs.get(terrain)
                if img is not None:
                    self._screen.blit(img, (px, py))
                else:
                    color = _TERRAIN_COLORS.get(terrain, (128, 128, 128))
                    pygame.draw.rect(self._screen, color, rect)

                # Grid lines
                pygame.draw.rect(self._screen, (40, 40, 40), rect, 1)

                # Road overlay
                if board.is_road(x, y):
                    road_rect = pygame.Rect(px + _CELL // 2 - 2, py + _CELL // 2 - 2, 4, 4)
                    pygame.draw.rect(self._screen, (180, 140, 80), road_rect)

        # Draw cities
        for tribe in tribes:
            tribe_color = tribe_colors[tribe.tribe_id]
            dark_color = tribe.get_type().get_color_dark()
            for city_id in tribe.get_cities_id():
                city = board.get_actor(city_id)
                if city is None:
                    continue
                pos = city.get_position()
                px, py = pos.x * _CELL, pos.y * _CELL
                # City border in tribe colour
                city_rect = pygame.Rect(px + 2, py + 2, _CELL - 4, _CELL - 4)
                pygame.draw.rect(self._screen, tribe_color, city_rect)
                pygame.draw.rect(self._screen, dark_color, city_rect, 2)
                # City level indicator
                lbl = self._font_sm.render(str(city.get_level()), True, (0, 0, 0))
                self._screen.blit(lbl, (px + 3, py + 3))

        # Draw units
        for tribe in tribes:
            tribe_color = tribe_colors[tribe.tribe_id]
            all_unit_ids: list[int] = []
            for city_id in tribe.get_cities_id():
                city = board.get_actor(city_id)
                if city is not None:
                    all_unit_ids.extend(city.get_units_id())
            all_unit_ids.extend(tribe.get_extra_units())

            for uid in all_unit_ids:
                unit = board.get_actor(uid)
                if unit is None:
                    continue
                pos = unit.get_position()
                px, py = pos.x * _CELL, pos.y * _CELL

                # Draw unit circle in tribe colour
                cx, cy = px + _CELL // 2, py + _CELL // 2
                radius = _CELL // 2 - 4
                pygame.draw.circle(self._screen, tribe_color, (cx, cy), radius)
                pygame.draw.circle(self._screen, (0, 0, 0), (cx, cy), radius, 1)

                # HP bar
                hp_ratio = unit.get_current_hp() / max(unit.get_max_hp(), 1)
                bar_w = _CELL - 8
                bar_h = 3
                bar_x = px + 4
                bar_y = py + _CELL - 5
                pygame.draw.rect(self._screen, (200, 0, 0),
                                 (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(self._screen, (0, 200, 0),
                                 (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

                # First letter of unit type
                unit_char = unit.get_type().name[0]
                lbl = self._font_sm.render(unit_char, True, (0, 0, 0))
                self._screen.blit(lbl, (cx - lbl.get_width() // 2,
                                        cy - lbl.get_height() // 2))

        # Highlight active tribe's capital region lightly
        active_id = gs.get_active_tribe_id()
        if active_id >= 0 and active_id < len(tribes):
            active_tribe = tribes[active_id]
            if active_tribe.get_cities_id():
                capital_id = active_tribe.get_cities_id()[0]
                capital = board.get_actor(capital_id)
                if capital is not None:
                    pos = capital.get_position()
                    hl_surf = pygame.Surface((_CELL, _CELL), pygame.SRCALPHA)
                    hl_surf.fill((255, 255, 255, 40))
                    self._screen.blit(hl_surf, (pos.x * _CELL, pos.y * _CELL))

    def _draw_side_panel(self) -> None:
        gs = self._gs
        ox = self._board_px  # x offset for side panel
        panel_rect = pygame.Rect(ox, 0, _SIDE_W, self._board_px + _INFO_H)
        pygame.draw.rect(self._screen, (30, 30, 40), panel_rect)

        y = 10
        # Turn counter
        tick_lbl = self._font_lg.render(f"Turn: {gs.get_tick()}", True, (220, 220, 220))
        self._screen.blit(tick_lbl, (ox + 10, y))
        y += 24

        # Active tribe
        active_id = gs.get_active_tribe_id()
        if active_id >= 0:
            tribe = gs.get_tribe(active_id)
            tribe_color = tribe.get_type().get_color()
            name_lbl = self._font_lg.render(f"Acting: {tribe.get_type().get_name()}", True, tribe_color)
            self._screen.blit(name_lbl, (ox + 10, y))
            y += 20
            stars_lbl = self._font_sm.render(
                f"Stars: {tribe.get_stars()} (+{tribe.get_max_production(gs)})", True, (200, 200, 180)
            )
            self._screen.blit(stars_lbl, (ox + 10, y))
            y += 18

        y += 10
        sep = self._font_sm.render("--- Rankings ---", True, (150, 150, 150))
        self._screen.blit(sep, (ox + 10, y))
        y += 18

        ranking = gs.get_current_ranking()
        tribes_list = gs.get_tribes()
        for rank_idx, tr in enumerate(ranking):
            if tr.id >= len(tribes_list):
                continue
            t_obj = tribes_list[tr.id]
            t_color = t_obj.get_type().get_color()
            status = _RESULT_LABEL.get(tr.result, "")
            line = f"#{rank_idx+1} {t_obj.get_type().get_name()}: {tr.score}pts {status}"
            lbl = self._font_sm.render(line, True, t_color)
            self._screen.blit(lbl, (ox + 10, y))
            y += 16

        # Last action info
        if self._last_action is not None:
            y += 10
            act_lbl = self._font_sm.render("Last action:", True, (150, 150, 150))
            self._screen.blit(act_lbl, (ox + 10, y))
            y += 14
            act_str = str(self._last_action)
            # Wrap long strings
            if len(act_str) > 30:
                act_str = act_str[:29] + "…"
            act_val = self._font_sm.render(act_str, True, (200, 200, 180))
            self._screen.blit(act_val, (ox + 10, y))

        # Controls hint at bottom of side panel
        hint_y = self._board_px + _INFO_H - 30
        hint = self._font_sm.render("Q / ESC: quit", True, (100, 100, 100))
        self._screen.blit(hint, (ox + 10, hint_y))

    def _draw_info_bar(self) -> None:
        gs = self._gs
        bar_rect = pygame.Rect(0, self._board_px, self._board_px, _INFO_H)
        pygame.draw.rect(self._screen, (25, 25, 35), bar_rect)

        y = self._board_px + 6
        tribes_list = gs.get_tribes()
        x = 6
        row_h = 28
        for tribe in tribes_list:
            t_color = tribe.get_type().get_color()
            t_dark = tribe.get_type().get_color_dark()
            block = pygame.Rect(x, y, _SIDE_W - 20, row_h - 2)
            pygame.draw.rect(self._screen, t_dark, block)
            pygame.draw.rect(self._screen, t_color, block, 1)

            status = _RESULT_LABEL.get(tribe.get_winner(), "")
            text = (f"{tribe.get_type().get_name()}: "
                    f"{tribe.get_score()}pts | "
                    f"cities={tribe.get_num_cities()} | "
                    f"stars={tribe.get_stars()} {status}")
            lbl = self._font_sm.render(text, True, t_color)
            self._screen.blit(lbl, (x + 4, y + 6))
            y += row_h
            if y + row_h > self._board_px + _INFO_H:
                break
