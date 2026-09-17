"""
src/screens/main_menu.py
========================
Main-menu screen for Brick Breaker.

Visual layout (800 x 600 window, Cave theme matching mock design):
  ┌────────────────────────────────────────┐
  │         [ BRICK BREAKER ]              │  <- Stone banner at top, y=44
  │                                        │
  │            [  START   ]                │  <- Stone slab button, y=224
  │            [ SETTINGS ]                │  <- Stone slab button, y=335
  │            [   EXIT   ]                │  <- Stone slab button, y=445
  └────────────────────────────────────────┘
Background: Cave mine scene with stalactites, mushrooms, crystals, and pickaxe.
"""

from __future__ import annotations

import os

import pygame

from src.config import (
    FONT_PRIMARY_PATH,
    FONT_SECONDARY_PATH,
    MAIN_MENU_BG_PATH,
    MAIN_MENU_BTN_PATH,
    MAIN_TITLE_PATH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.core.audio import play_music, stop_music
from src.core.states import GameState
from src.ui.button import MenuButton

# ---------------------------------------------------------------------------
# Layout & styling constants (800 x 600 logical resolution)
# ---------------------------------------------------------------------------
_TITLE_W = 525
_TITLE_H = 134
_TITLE_X = (SCREEN_WIDTH - _TITLE_W) // 2
_TITLE_Y = 44

_BTN_W = 259
_BTN_H = 95
_BTN_X = (SCREEN_WIDTH - _BTN_W) // 2
_BTN_Y_START = 224
_BTN_GAP = 16
_BTN_FONT_SIZE = 42

_BTN_COLOR_NORMAL = (66, 19, 14)
_BTN_COLOR_HOVER = (135, 36, 26)


class MainMenu:
    """Main-menu screen with stone buttons and cave background."""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._next_state: GameState | None = None
        self._selected_index: int = 0

        # ── background ────────────────────────────────────────────────────
        self._bg: pygame.Surface
        if os.path.exists(MAIN_MENU_BG_PATH):
            raw_bg = pygame.image.load(MAIN_MENU_BG_PATH).convert()
            if raw_bg.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
                self._bg = pygame.transform.smoothscale(raw_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            else:
                self._bg = raw_bg
        else:
            self._bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self._bg.fill((35, 25, 30))

        # ── title banner ──────────────────────────────────────────────────
        self._title_surf: pygame.Surface | None = None
        self._title_rect = pygame.Rect(_TITLE_X, _TITLE_Y, _TITLE_W, _TITLE_H)
        if os.path.exists(MAIN_TITLE_PATH):
            raw_title = pygame.image.load(MAIN_TITLE_PATH).convert_alpha()
            if raw_title.get_size() != (_TITLE_W, _TITLE_H):
                self._title_surf = pygame.transform.smoothscale(raw_title, (_TITLE_W, _TITLE_H))
            else:
                self._title_surf = raw_title

        # ── fonts ─────────────────────────────────────────────────────────
        if os.path.exists(FONT_PRIMARY_PATH):
            self._btn_font = pygame.font.Font(FONT_PRIMARY_PATH, _BTN_FONT_SIZE)
        elif os.path.exists(FONT_SECONDARY_PATH):
            self._btn_font = pygame.font.Font(FONT_SECONDARY_PATH, _BTN_FONT_SIZE)
        else:
            self._btn_font = pygame.font.Font(None, _BTN_FONT_SIZE)

        # ── button surface ────────────────────────────────────────────────
        btn_bg_surf: pygame.Surface | None = None
        if os.path.exists(MAIN_MENU_BTN_PATH):
            raw_btn = pygame.image.load(MAIN_MENU_BTN_PATH).convert_alpha()
            if raw_btn.get_size() != (_BTN_W, _BTN_H):
                btn_bg_surf = pygame.transform.smoothscale(raw_btn, (_BTN_W, _BTN_H))
            else:
                btn_bg_surf = raw_btn

        # ── buttons ───────────────────────────────────────────────────────
        button_defs: list[tuple[str, GameState]] = [
            ("START", GameState.PLAYING),
            ("SETTINGS", GameState.SETTINGS),
            ("EXIT", GameState.QUIT),
        ]

        self._buttons: list[tuple[MenuButton, GameState]] = []
        for i, (label, state) in enumerate(button_defs):
            rect = pygame.Rect(
                _BTN_X,
                _BTN_Y_START + i * (_BTN_H + _BTN_GAP),
                _BTN_W,
                _BTN_H,
            )
            btn = MenuButton(
                rect=rect,
                label=label,
                bg_surface=btn_bg_surf,
                font=self._btn_font,
                text_color=_BTN_COLOR_NORMAL,
                hover_text_color=_BTN_COLOR_HOVER,
            )
            self._buttons.append((btn, state))

        # ── audio ─────────────────────────────────────────────────────────
        self.play_bgm()

    # ------------------------------------------------------------------
    # Audio interface
    # ------------------------------------------------------------------

    def play_bgm(self) -> None:
        """Start playing main-menu background music on loop."""
        play_music()

    def stop_bgm(self) -> None:
        """Stop main-menu background music."""
        stop_music()

    # ------------------------------------------------------------------
    # Game-loop interface
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Process input events (mouse clicks and keyboard navigation)."""
        # Mouse interactions
        for i, (btn, state) in enumerate(self._buttons):
            if btn.update(events):
                self._selected_index = i
                self._next_state = state

        # Keyboard fallback navigation
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    self._selected_index = (self._selected_index - 1) % len(self._buttons)
                    self._update_keyboard_selection()
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self._selected_index = (self._selected_index + 1) % len(self._buttons)
                    self._update_keyboard_selection()
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    _, state = self._buttons[self._selected_index]
                    self._next_state = state
                elif ev.key == pygame.K_ESCAPE:
                    self._next_state = GameState.QUIT

    def _update_keyboard_selection(self) -> None:
        """Update hover state on buttons according to keyboard focus."""
        for i, (btn, _) in enumerate(self._buttons):
            btn._hovered = i == self._selected_index

    def update(self, dt: float) -> None:
        """Advance menu animations or state transitions."""
        del dt  # Unused for static background frame

    def draw(self) -> None:
        """Render background, title banner, and buttons."""
        # 1. Cave background frame
        self._screen.blit(self._bg, (0, 0))

        # 2. Title banner
        if self._title_surf is not None:
            self._screen.blit(self._title_surf, self._title_rect.topleft)

        # 3. Interactive stone buttons
        for btn, _ in self._buttons:
            btn.draw(self._screen)

    @property
    def next_state(self) -> GameState | None:
        """Next GameState requested by user interaction, or None."""
        return self._next_state
