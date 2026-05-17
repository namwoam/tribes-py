"Pygame-based GUI for Tribes-py, replacing the Java Swing GUI."

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from tribes.types import BUILDING, RESULT, TERRAIN

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

_TERRAIN_COLORS: dict[TERRAIN, tuple[int, int, int]] = {
    TERRAIN.PLAIN: (200, 210, 150),
    TERRAIN.SHALLOW_WATER: (100, 180, 240),
    TERRAIN.DEEP_WATER: (30, 90, 180),
    TERRAIN.MOUNTAIN: (140, 120, 90),
    TERRAIN.VILLAGE: (230, 200, 120),
    TERRAIN.CITY: (210, 140, 60),
    TERRAIN.FOREST: (60, 140, 60),
    TERRAIN.FOG: (80, 80, 80),
}

_RESULT_LABEL: dict[RESULT, str] = {
    RESULT.WIN: "WIN",
    RESULT.LOSS: "LOSS",
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
    _IMG_CACHE[key] = None  # type: ignore[assignment]
    return None  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

_CELL = 40  # pixels per tile
_SIDE_W = 260  # side-panel width
_INFO_H = 160  # bottom info-bar height
_FPS = 30
_SCROLL_SPEED = 15  # pixels per frame when holding an arrow key
_INIT_W = 900  # initial window width
_INIT_H = 700  # initial window height


class GUI:
    """Top-down pygame rendering of a Tribes game with scrollable viewport."""

    def __init__(self, game: Game, title: str = "Tribes") -> None:
        if not _HAS_PYGAME:
            raise RuntimeError("pygame is required for the GUI.")

        pygame.init()
        pygame.display.set_caption(title)

        self._game = game
        self._closed = False
        self._gs: Optional[GameState] = None
        self._last_action: Optional[Action] = None

        board = game.get_board()
        self._grid = board.get_size()
        self._board_px = self._grid * _CELL  # total board canvas size

        # Scroll offset (top-left corner of the viewport in board-pixel space)
        self._scroll_x = 0
        self._scroll_y = 0

        # Mouse-drag state
        self._drag_start: Optional[tuple[int, int]] = None
        self._drag_scroll_start: tuple[int, int] = (0, 0)

        self._screen = pygame.display.set_mode((_INIT_W, _INIT_H), pygame.RESIZABLE)
        self._clock = pygame.time.Clock()

        self._font_lg = pygame.font.SysFont("monospace", 14, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 11)

        # Pre-load terrain images
        self._terrain_imgs: dict[TERRAIN, Optional[pygame.Surface]] = {}
        for t in TERRAIN:
            self._terrain_imgs[t] = _load_image(t._image_file, (_CELL, _CELL))

        self._unit_img_cache: dict[str, Optional[pygame.Surface]] = {}

        _city_files = {
            "small": "img/terrain/city.png",
            "large": "img/terrain/city3.png",
        }
        self._city_imgs = {
            k: _load_image(v, (_CELL, _CELL)) for k, v in _city_files.items()
        }

        self._building_imgs: dict[BUILDING, Optional[pygame.Surface]] = {}
        for b in BUILDING:
            self._building_imgs[b] = _load_image(b._image_file, (_CELL, _CELL))

    # ------------------------------------------------------------------
    # Viewport helpers
    # ------------------------------------------------------------------

    @property
    def _viewport_w(self) -> int:
        return max(1, self._screen.get_width() - _SIDE_W)

    @property
    def _viewport_h(self) -> int:
        return max(1, self._screen.get_height() - _INFO_H)

    def _clamp_scroll(self) -> None:
        max_sx = max(0, self._board_px - self._viewport_w)
        max_sy = max(0, self._board_px - self._viewport_h)
        self._scroll_x = max(0, min(self._scroll_x, max_sx))
        self._scroll_y = max(0, min(self._scroll_y, max_sy))

    # ------------------------------------------------------------------
    # City border drawing helper
    # ------------------------------------------------------------------

    def _draw_city_borders(
        self,
        board,
        size: int,
        tribe_colors: dict,
        scroll_x: int,
        scroll_y: int,
    ) -> None:
        """Draw dotted territory borders for each city."""
        city_color: dict[int, tuple] = {}
        for tribe in board.get_tribes():
            color = tribe_colors.get(tribe.tribe_id, (200, 200, 200))
            for city_id in tribe.get_cities_id():
                city_color[city_id] = color

        dot = 3
        gap = 3

        for x in range(size):
            for y in range(size):
                cid = board.get_city_id_at(x, y)
                if cid == -1:
                    continue
                color = city_color.get(cid, (200, 200, 200))
                px = x * _CELL - scroll_x
                py = y * _CELL - scroll_y

                # right edge
                r_cid = board.get_city_id_at(x + 1, y) if x + 1 < size else -1
                if r_cid != cid:
                    ex = px + _CELL - 1
                    p = 0
                    while p < _CELL:
                        pygame.draw.rect(
                            self._screen, color, (ex, py + p, 2, min(dot, _CELL - p))
                        )
                        p += dot + gap

                # bottom edge
                b_cid = board.get_city_id_at(x, y + 1) if y + 1 < size else -1
                if b_cid != cid:
                    ey = py + _CELL - 1
                    p = 0
                    while p < _CELL:
                        pygame.draw.rect(
                            self._screen, color, (px + p, ey, min(dot, _CELL - p), 2)
                        )
                        p += dot + gap

                # left edge
                l_cid = board.get_city_id_at(x - 1, y) if x - 1 >= 0 else -1
                if l_cid != cid:
                    p = 0
                    while p < _CELL:
                        pygame.draw.rect(
                            self._screen, color, (px, py + p, 2, min(dot, _CELL - p))
                        )
                        p += dot + gap

                # top edge
                t_cid = board.get_city_id_at(x, y - 1) if y - 1 >= 0 else -1
                if t_cid != cid:
                    p = 0
                    while p < _CELL:
                        pygame.draw.rect(
                            self._screen, color, (px + p, py, min(dot, _CELL - p), 2)
                        )
                        p += dot + gap

    def _get_unit_image(self, unit) -> "Optional[pygame.Surface]":
        folder = unit.get_type()._image_file  # e.g. "img/unit/warrior/"
        tid = unit.tribe_id
        suffix = "Exhausted" if unit.is_finished() else ""
        key = f"{folder}{tid}{suffix}"
        if key in self._unit_img_cache:
            return self._unit_img_cache[key]
        img = _load_image(f"{folder}{tid}{suffix}.png", (_CELL, _CELL))
        if img is None:
            # Fall back to tribe 0's sprite when tribe-specific image is missing
            img = _load_image(f"{folder}0{suffix}.png", (_CELL, _CELL))
        self._unit_img_cache[key] = img
        return img

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

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    self._closed = True

            elif event.type == pygame.VIDEORESIZE:
                self._screen = pygame.display.set_mode(
                    (event.w, event.h), pygame.RESIZABLE
                )
                self._clamp_scroll()

            elif event.type == pygame.MOUSEWHEEL:
                self._scroll_x += event.x * _SCROLL_SPEED * 3
                self._scroll_y -= event.y * _SCROLL_SPEED * 3
                self._clamp_scroll()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    if mx < self._viewport_w and my < self._viewport_h:
                        self._drag_start = event.pos
                        self._drag_scroll_start = (self._scroll_x, self._scroll_y)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self._drag_start = None

            elif event.type == pygame.MOUSEMOTION:
                if self._drag_start is not None:
                    dx = self._drag_start[0] - event.pos[0]
                    dy = self._drag_start[1] - event.pos[1]
                    self._scroll_x = self._drag_scroll_start[0] + dx
                    self._scroll_y = self._drag_scroll_start[1] + dy
                    self._clamp_scroll()

        # Continuous scroll from held arrow / WASD keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._scroll_x -= _SCROLL_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._scroll_x += _SCROLL_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self._scroll_y -= _SCROLL_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self._scroll_y += _SCROLL_SPEED
        self._clamp_scroll()

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
        sx, sy = self._scroll_x, self._scroll_y
        vw, vh = self._viewport_w, self._viewport_h

        # Build a quick tribe-id → color map
        tribe_colors: dict[int, tuple[int, int, int]] = {}
        for tribe in tribes:
            tribe_colors[tribe.tribe_id] = tribe.get_type().get_color()

        # Clip drawing to the viewport rectangle
        self._screen.set_clip(pygame.Rect(0, 0, vw, vh))

        # Only iterate over visible tiles
        start_x = max(0, sx // _CELL)
        start_y = max(0, sy // _CELL)
        end_x = min(size, (sx + vw) // _CELL + 2)
        end_y = min(size, (sy + vh) // _CELL + 2)

        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                px = x * _CELL - sx
                py = y * _CELL - sy
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
                    road_rect = pygame.Rect(
                        px + _CELL // 2 - 2, py + _CELL // 2 - 2, 4, 4
                    )
                    pygame.draw.rect(self._screen, (180, 140, 80), road_rect)

                # Building overlay (full tile)
                building = board.get_building_at(x, y)
                if building is not None:
                    bimg = self._building_imgs.get(building)
                    if bimg is not None:
                        self._screen.blit(bimg, (px, py))
                    else:
                        pygame.draw.rect(
                            self._screen,
                            (200, 160, 60),
                            pygame.Rect(px, py, _CELL, _CELL),
                        )

        # Draw cities
        for tribe in tribes:
            tribe_color = tribe_colors[tribe.tribe_id]
            for city_id in tribe.get_cities_id():
                city = board.get_actor(city_id)
                if city is None:
                    continue
                pos = city.get_position()
                px = pos.x * _CELL - sx
                py = pos.y * _CELL - sy
                level = city.get_level()
                city_img = self._city_imgs["large" if level >= 3 else "small"]
                city_rect = pygame.Rect(px, py, _CELL, _CELL)
                if city_img is not None:
                    self._screen.blit(city_img, (px, py))
                else:
                    pygame.draw.rect(self._screen, tribe_color, city_rect)
                pygame.draw.rect(self._screen, tribe_color, city_rect, 2)
                lbl = self._font_sm.render(str(level), True, (255, 255, 255))
                self._screen.blit(lbl, (px + 3, py + 3))
                unit_limit = level + 1
                unit_lbl = self._font_sm.render(
                    f"{city.get_num_units()}/{unit_limit}", True, (255, 255, 255)
                )
                self._screen.blit(
                    unit_lbl, (px + 3, py + _CELL - unit_lbl.get_height() - 2)
                )

        # Draw city territory borders (clip still active)
        self._draw_city_borders(board, size, tribe_colors, sx, sy)

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
                px = pos.x * _CELL - sx
                py = pos.y * _CELL - sy

                unit_img = self._get_unit_image(unit)
                cx, cy = px + _CELL // 2, py + _CELL // 2
                if unit_img is not None:
                    self._screen.blit(unit_img, (px, py))
                else:
                    radius = _CELL // 2 - 4
                    pygame.draw.circle(self._screen, tribe_color, (cx, cy), radius)
                    pygame.draw.circle(self._screen, (0, 0, 0), (cx, cy), radius, 1)
                    unit_char = unit.get_type().name[0]
                    lbl = self._font_sm.render(unit_char, True, (0, 0, 0))
                    self._screen.blit(
                        lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2)
                    )

                # HP bar
                hp_ratio = unit.get_current_hp() / max(unit.get_max_hp(), 1)
                bar_w = _CELL - 8
                bar_h = 3
                bar_x = px + 4
                bar_y = py + _CELL - 5
                pygame.draw.rect(
                    self._screen, (200, 0, 0), (bar_x, bar_y, bar_w, bar_h)
                )
                pygame.draw.rect(
                    self._screen,
                    (0, 200, 0),
                    (bar_x, bar_y, int(bar_w * hp_ratio), bar_h),
                )

        # Highlight active tribe's capital
        active_id = gs.get_active_tribe_id()
        tribes_list = gs.get_tribes()
        if 0 <= active_id < len(tribes_list):
            active_tribe = tribes_list[active_id]
            if active_tribe.get_cities_id():
                capital_id = active_tribe.get_cities_id()[0]
                capital = board.get_actor(capital_id)
                if capital is not None:
                    pos = capital.get_position()
                    hl_surf = pygame.Surface((_CELL, _CELL), pygame.SRCALPHA)
                    hl_surf.fill((255, 255, 255, 40))
                    self._screen.blit(
                        hl_surf,
                        (pos.x * _CELL - sx, pos.y * _CELL - sy),
                    )

        self._screen.set_clip(None)

        # Scroll position indicator (thin bar along bottom of viewport)
        max_sx = max(1, self._board_px - vw)
        max_sy = max(1, self._board_px - vh)
        if max_sx > 0:
            bar_total = vw
            thumb_w = max(20, int(bar_total * vw / self._board_px))
            thumb_x = int((bar_total - thumb_w) * sx / max_sx)
            pygame.draw.rect(self._screen, (60, 60, 60), (0, vh - 6, vw, 6))
            pygame.draw.rect(
                self._screen, (120, 120, 120), (thumb_x, vh - 6, thumb_w, 6)
            )
        if max_sy > 0:
            bar_total = vh
            thumb_h = max(20, int(bar_total * vh / self._board_px))
            thumb_y = int((bar_total - thumb_h) * sy / max_sy)
            pygame.draw.rect(self._screen, (60, 60, 60), (vw - 6, 0, 6, vh))
            pygame.draw.rect(
                self._screen, (120, 120, 120), (vw - 6, thumb_y, 6, thumb_h)
            )

    def _draw_side_panel(self) -> None:
        gs = self._gs
        vw = self._viewport_w
        vh = self._viewport_h
        panel_h = vh + _INFO_H
        panel_rect = pygame.Rect(vw, 0, _SIDE_W, panel_h)
        pygame.draw.rect(self._screen, (30, 30, 40), panel_rect)

        y = 10
        tick_lbl = self._font_lg.render(f"Turn: {gs.get_tick()}", True, (220, 220, 220))
        self._screen.blit(tick_lbl, (vw + 10, y))
        y += 24

        active_id = gs.get_active_tribe_id()
        if active_id >= 0:
            tribe = gs.get_tribe(active_id)
            tribe_color = tribe.get_type().get_color()
            name_lbl = self._font_lg.render(
                f"Acting: {tribe.get_type().get_name()}", True, tribe_color
            )
            self._screen.blit(name_lbl, (vw + 10, y))
            y += 20
            stars_lbl = self._font_sm.render(
                f"Stars: {tribe.get_stars()} (+{tribe.get_max_production(gs)})",
                True,
                (200, 200, 180),
            )
            self._screen.blit(stars_lbl, (vw + 10, y))
            y += 18

        y += 10
        sep = self._font_sm.render("--- Rankings ---", True, (150, 150, 150))
        self._screen.blit(sep, (vw + 10, y))
        y += 18

        ranking = gs.get_current_ranking()
        tribes_list = gs.get_tribes()
        for rank_idx, tr in enumerate(ranking):
            if tr.id >= len(tribes_list):
                continue
            t_obj = tribes_list[tr.id]
            t_color = t_obj.get_type().get_color()
            status = _RESULT_LABEL.get(tr.result, "")
            line = (
                f"#{rank_idx+1} {t_obj.get_type().get_name()}: {tr.score}pts {status}"
            )
            lbl = self._font_sm.render(line, True, t_color)
            self._screen.blit(lbl, (vw + 10, y))
            y += 16

        if self._last_action is not None:
            y += 10
            act_lbl = self._font_sm.render("Last action:", True, (150, 150, 150))
            self._screen.blit(act_lbl, (vw + 10, y))
            y += 14
            act_str = str(self._last_action)
            if len(act_str) > 30:
                act_str = act_str[:29] + "…"
            act_val = self._font_sm.render(act_str, True, (200, 200, 180))
            self._screen.blit(act_val, (vw + 10, y))

        hint_y = panel_h - 46
        hints = [
            "Arrows/WASD: scroll",
            "Mouse drag / wheel: scroll",
            "Q / ESC: quit",
        ]
        for hint in hints:
            h_lbl = self._font_sm.render(hint, True, (100, 100, 100))
            self._screen.blit(h_lbl, (vw + 10, hint_y))
            hint_y += 14

    def _draw_info_bar(self) -> None:
        gs = self._gs
        vw = self._viewport_w
        vh = self._viewport_h
        bar_rect = pygame.Rect(0, vh, vw, _INFO_H)
        pygame.draw.rect(self._screen, (25, 25, 35), bar_rect)

        y = vh + 6
        tribes_list = gs.get_tribes()
        x = 6
        row_h = 28
        max_w = vw - x * 2
        max_score = max((t.get_score() for t in tribes_list), default=1)
        for tribe in tribes_list:
            t_color = tribe.get_type().get_color()
            t_dark = tribe.get_type().get_color_dark()
            score = tribe.get_score()
            bar_w = int(max_w * score / max_score) if max_score > 0 else max_w
            bar_w = max(bar_w, 4)
            pygame.draw.rect(self._screen, t_dark, pygame.Rect(x, y, max_w, row_h - 2))
            pygame.draw.rect(self._screen, t_color, pygame.Rect(x, y, bar_w, row_h - 2))
            pygame.draw.rect(
                self._screen, (0, 0, 0), pygame.Rect(x, y, max_w, row_h - 2), 1
            )

            status = _RESULT_LABEL.get(tribe.get_winner(), "")
            text = (
                f"{tribe.get_type().get_name()}: "
                f"{score}pts | "
                f"cities={tribe.get_num_cities()} | "
                f"stars={tribe.get_stars()} {status}"
            )
            lbl = self._font_sm.render(text, True, (0, 0, 0))
            self._screen.blit(lbl, (x + 4, y + 6))
            y += row_h
            if y + row_h > vh + _INFO_H:
                break
