"""
src/screens/main_menu.py
========================
Main-menu screen for Brick Breaker.

Visual layout (800 x 600 window):
  ┌────────────────────────────────┐
  │       [  BRICK BREAKER  ]      │  <- thick-outline wood panel, y=60
  │                                │
  │          [ START  ]            │  <- thin-outline beige button, y=282
  │          [SETTINGS]            │                                  y=376
  │          [ EXIT   ]            │                                  y=470
  └────────────────────────────────┘
Background: animated cloud GIF (no audio).
"""

from __future__ import annotations

import os

import pygame

from src.config import SCREEN_HEIGHT, SCREEN_WIDTH
from src.core.states import GameState
from src.ui.button import MenuButton
from src.ui.gif_background import GifBackground
from src.ui.nine_slice import NineSlicePanel

# ---------------------------------------------------------------------------
# Asset paths (relative to repo root)
# ---------------------------------------------------------------------------
_TILE_THICK = "assets/sprites/ui/kenney_pixel_adventure/tiles/large/thick_outline"
_TITLE_BG_IMG = "assets/sprites/ui/menu/main_title_bg.png"
_BTN_BG_IMG = "assets/sprites/ui/menu/main_menu_btn_bg.png"
_BG_GIF = "assets/backgrounds/Clouds_drifting_in_blue_sky.gif"
_FONT_TITLE = "assets/fonts/ThaleahFat.ttf"
_FONT_BTN = "assets/fonts/Minecraft.ttf"

# ---------------------------------------------------------------------------
# Layout (all in screen pixels, tuned to match mockup at 800x600)
# ---------------------------------------------------------------------------
_TITLE_PANEL_W = 520
_TITLE_PANEL_Y = 45
_TITLE_FONT_SIZE = 72

_BTN_W = 260
_BTN_GAP = 14
_BTN_FONT_SIZE = 28
_BTN_TEXT_COLOR = (75, 42, 7)

# ---------------------------------------------------------------------------
# Title text colours (matching mockup: bright red body, white thin highlight,
# dark maroon shadow/outline)
# ---------------------------------------------------------------------------
_TITLE_COLOR = (214, 48, 48)  # vivid red body
_TITLE_SHADOW_COLOR = (90, 15, 15)  # dark maroon, 3 px offset
_TITLE_HILIGHT_COLR = (255, 160, 160)  # pinkish-white inner highlight, -1 px offset


class MainMenu:
    """Self-contained main-menu screen driven by the game loop."""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._next_state: GameState | None = None

        # ── background ────────────────────────────────────────────────────
        self._bg = GifBackground(_BG_GIF, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # ── fonts ─────────────────────────────────────────────────────────
        self._title_font = pygame.font.Font(_FONT_TITLE, _TITLE_FONT_SIZE)
        self._btn_font = pygame.font.Font(_FONT_BTN, _BTN_FONT_SIZE)

        # ── title panel ───────────────────────────────────────────────────
        self._title_bg: pygame.Surface | None = None
        self._thick_panel: NineSlicePanel | None = None

        if os.path.exists(_TITLE_BG_IMG):
            raw_title = pygame.image.load(_TITLE_BG_IMG).convert_alpha()
            t_bbox = raw_title.get_bounding_rect()
            title_sub = (
                raw_title.subsurface(t_bbox).copy()
                if t_bbox.width > 0 and t_bbox.height > 0
                else raw_title
            )
            tw = _TITLE_PANEL_W
            th = int(tw * (title_sub.get_height() / title_sub.get_width()))
            self._title_bg = pygame.transform.smoothscale(title_sub, (tw, th))
            self._title_rect = pygame.Rect((SCREEN_WIDTH - tw) // 2, _TITLE_PANEL_Y, tw, th)
        else:
            self._thick_panel = NineSlicePanel(_TILE_THICK, scale=2)
            self._title_rect = pygame.Rect((SCREEN_WIDTH - 560) // 2, 58, 560, 112)

        # Pre-render title text surfaces
        self._title_shadow = self._title_font.render("BRICK BREAKER", True, _TITLE_SHADOW_COLOR)
        self._title_surf = self._title_font.render("BRICK BREAKER", True, _TITLE_COLOR)
        self._title_hilit = self._title_font.render("BRICK BREAKER", True, _TITLE_HILIGHT_COLR)

        # ── button background ─────────────────────────────────────────────
        raw_btn = pygame.image.load(_BTN_BG_IMG).convert_alpha()
        b_bbox = raw_btn.get_bounding_rect()
        btn_sub = (
            raw_btn.subsurface(b_bbox).copy() if b_bbox.width > 0 and b_bbox.height > 0 else raw_btn
        )

        btn_w = _BTN_W
        btn_h = int(btn_w * (btn_sub.get_height() / btn_sub.get_width()))
        cx = (SCREEN_WIDTH - btn_w) // 2
        start_y = self._title_rect.bottom + 40

        self._buttons: list[tuple[MenuButton, GameState]] = []
        for i, (label, state) in enumerate(
            [
                ("START", GameState.PLAYING),
                ("SETTINGS", GameState.SETTINGS),
                ("EXIT", GameState.QUIT),
            ]
        ):
            rect = pygame.Rect(
                cx,
                start_y + i * (btn_h + _BTN_GAP),
                btn_w,
                btn_h,
            )
            btn = MenuButton(
                rect=rect,
                label=label,
                bg_surface=btn_sub,
                font=self._btn_font,
                text_color=_BTN_TEXT_COLOR,
            )
            self._buttons.append((btn, state))

    # ------------------------------------------------------------------
    # Game-loop interface
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Feed pygame events; triggers state change on button click."""
        for btn, state in self._buttons:
            if btn.update(events):
                self._next_state = state

    def update(self, dt: float) -> None:
        """Advance background animation."""
        self._bg.update(dt)

    def draw(self) -> None:
        """Render all layers to the screen."""
        # 1. Animated cloud background
        self._bg.draw(self._screen)

        # 2. Title panel
        if self._title_bg is not None:
            self._screen.blit(self._title_bg, self._title_rect.topleft)
        elif self._thick_panel is not None:
            self._thick_panel.draw(self._screen, self._title_rect)
        self._draw_title()

        # 3. Buttons
        for btn, _ in self._buttons:
            btn.draw(self._screen)

    @property
    def next_state(self) -> GameState | None:
        """Next GameState requested by user interaction, or None."""
        return self._next_state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw_title(self) -> None:
        """Composite the title text with shadow and subtle highlight."""
        cx, cy = self._title_rect.center

        # Dark maroon shadow (+3, +3)
        shadow_r = self._title_shadow.get_rect(center=(cx + 3, cy + 3))
        self._screen.blit(self._title_shadow, shadow_r)

        # Main red text
        title_r = self._title_surf.get_rect(center=(cx, cy))
        self._screen.blit(self._title_surf, title_r)

        # Subtle pink highlight (-1, -2) -> upper-left inner glow effect
        hilit_r = self._title_hilit.get_rect(center=(cx - 1, cy - 2))
        self._screen.blit(self._title_hilit, hilit_r)
