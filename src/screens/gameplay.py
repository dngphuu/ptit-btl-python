"""
src/screens/gameplay.py
=======================
Main gameplay screen for Brick Breaker.

Visual layout (800 x 600 logical resolution, matching mock design):
  ┌────────────────────────────────────────────────────────┐
  │ [PAUSE]       [ SCORE   LEVEL   LIVES ]         [EXIT] │  <- Top header UI
  │ (20, 20)          (144, 46, 516, 136)         (684, 20)│
  │                                                        │
  │               ┌───────────────────────┐                │
  │               │   BRICKS & PLAYFIELD  │                │
  │               │                       │                │
  │               │        o BALL         │                │
  │               │       ════ PADDLE     │                │
  │               └───────────────────────┘                │
  │                      [LANTERN]                         │
  └────────────────────────────────────────────────────────┘
Background: Cave mine scene with hieroglyph borders and glowing lantern.
"""

from __future__ import annotations

import os

import pygame

from src.config import (
    FONT_PRIMARY_PATH,
    FONT_SECONDARY_PATH,
    GAME_BGM_PATH,
    GAME_BGM_VOLUME,
    GAME_EXIT_BTN_PATH,
    GAME_EXIT_BTN_RECT,
    GAME_HUD_RECT,
    GAME_PAUSE_BTN_PATH,
    GAME_PAUSE_BTN_RECT,
    HEART_ICON_PATH,
    HEART_SHEET_PATH,
    MAIN_GAME_BG_PATH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.core.audio import play_music, stop_music
from src.core.states import GameState
from src.entities import Brick, BrickGrid, BrickRenderer, Playfield
from src.ui.button import MenuButton

# HUD styling
_HUD_TEXT_COLOR = (66, 50, 45)
_HUD_LABEL_SIZE = 22
_HUD_VALUE_SIZE = 34


class GameplayScreen:
    """Main gameplay screen containing frame background, HUD, and control buttons."""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._next_state: GameState | None = None
        self._is_paused: bool = False

        # Gameplay session values (ready for entity integration)
        self.score: int = 0
        self.level_str: str = "1-1"
        self.lives: int = 3

        # ── Background Frame ──────────────────────────────────────────────
        self._bg: pygame.Surface
        if os.path.exists(MAIN_GAME_BG_PATH):
            raw_bg = pygame.image.load(MAIN_GAME_BG_PATH).convert()
            if raw_bg.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
                self._bg = pygame.transform.smoothscale(raw_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            else:
                self._bg = raw_bg
        else:
            self._bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self._bg.fill((30, 22, 26))

        # ── Fonts ─────────────────────────────────────────────────────────
        font_path = None
        if os.path.exists(FONT_SECONDARY_PATH):
            font_path = FONT_SECONDARY_PATH
        elif os.path.exists(FONT_PRIMARY_PATH):
            font_path = FONT_PRIMARY_PATH

        self._hud_lbl_font = pygame.font.Font(font_path, _HUD_LABEL_SIZE)
        self._hud_val_font = pygame.font.Font(font_path, _HUD_VALUE_SIZE)

        # ── Exit Button ───────────────────────────────────────────────────
        exit_rect = pygame.Rect(*GAME_EXIT_BTN_RECT)
        exit_surf: pygame.Surface | None = None
        if os.path.exists(GAME_EXIT_BTN_PATH):
            raw_exit = pygame.image.load(GAME_EXIT_BTN_PATH).convert_alpha()
            exit_surf = (
                pygame.transform.smoothscale(raw_exit, exit_rect.size)
                if raw_exit.get_size() != exit_rect.size
                else raw_exit
            )

        self.exit_button = MenuButton(
            rect=exit_rect,
            label="",
            bg_surface=exit_surf,
            press_offset=2,
        )

        # ── Pause Button ──────────────────────────────────────────────────
        pause_rect = pygame.Rect(*GAME_PAUSE_BTN_RECT)
        pause_surf: pygame.Surface | None = None
        if os.path.exists(GAME_PAUSE_BTN_PATH):
            raw_pause = pygame.image.load(GAME_PAUSE_BTN_PATH).convert_alpha()
            pause_surf = (
                pygame.transform.smoothscale(raw_pause, pause_rect.size)
                if raw_pause.get_size() != pause_rect.size
                else raw_pause
            )

        self.pause_button = MenuButton(
            rect=pause_rect,
            label="",
            bg_surface=pause_surf,
            press_offset=2,
        )

        # ── Heart Icon (for Lives HUD) ────────────────────────────────────
        self._heart_surf: pygame.Surface | None = None
        self._heart_dim_surf: pygame.Surface | None = None
        self.max_lives: int = 3

        heart_crop_rect = pygame.Rect(41, 40, 41, 41)
        raw_heart: pygame.Surface | None = None
        if os.path.exists(HEART_ICON_PATH):
            raw_heart = pygame.image.load(HEART_ICON_PATH).convert_alpha()
        elif os.path.exists(HEART_SHEET_PATH):
            sheet = pygame.image.load(HEART_SHEET_PATH).convert_alpha()
            raw_heart = sheet.subsurface(heart_crop_rect).copy()

        if raw_heart is not None:
            self._heart_surf = pygame.transform.smoothscale(raw_heart, (28, 28))
            self._heart_dim_surf = self._heart_surf.copy()
            self._heart_dim_surf.fill((120, 120, 120, 90), special_flags=pygame.BLEND_RGBA_MULT)

        # ── Playfield & Brick Wall Architecture ───────────────────────────
        self.playfield: Playfield = Playfield()
        self.brick_grid: BrickGrid = BrickGrid(self.playfield)
        self.brick_renderer: BrickRenderer = BrickRenderer()

        from src.entities.debris import DebrisManager
        self.debris_manager: DebrisManager = DebrisManager()

    @property
    def _bricks(self) -> list[Brick]:
        """Convenience property for backward compatibility."""
        return self.brick_grid.alive_bricks()

    # ------------------------------------------------------------------
    # State interface
    # ------------------------------------------------------------------

    @property
    def next_state(self) -> GameState | None:
        """Next GameState requested by gameplay interaction, or None."""
        return self._next_state

    def reset_state(self) -> None:
        """Reset requested state transition and revive the brick grid."""
        self._next_state = None
        self.brick_grid.reset()

    @property
    def is_paused(self) -> bool:
        """Whether gameplay is currently paused."""
        return self._is_paused

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        self._is_paused = not self._is_paused

    # ------------------------------------------------------------------
    # Audio interface
    # ------------------------------------------------------------------

    def play_bgm(self) -> None:
        """Start playing gameplay background music if available."""
        if os.path.exists(GAME_BGM_PATH):
            play_music(GAME_BGM_PATH, GAME_BGM_VOLUME)
        else:
            stop_music()

    def stop_bgm(self) -> None:
        """Stop gameplay background music."""
        stop_music()

    # ------------------------------------------------------------------
    # Game-loop interface
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Process input events for the gameplay screen."""
        # Exit button click -> return to main menu
        if self.exit_button.update(events):
            self._next_state = GameState.MAIN_MENU

        # Pause button click -> toggle pause
        if self.pause_button.update(events):
            self.toggle_pause()

        # Keyboard fallback navigation
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self._next_state = GameState.MAIN_MENU
                elif ev.key == pygame.K_p:
                    self.toggle_pause()

    def update(self, dt: float) -> None:
        """Advance gameplay logic and animations."""
        del dt  # Core physics will consume dt in future task
        if self._is_paused:
            return
        
        self.debris_manager.update()

    def draw(self) -> None:
        """Render frame background, HUD panel contents, and UI buttons."""
        # 1. Background frame
        self._screen.blit(self._bg, (0, 0))

        # 2. Top HUD banner text
        self._draw_hud()

        # 3. Brick grid (drawn via BrickRenderer)
        self.brick_renderer.render(self._screen, self.brick_grid)
        
        # 3.5. Debris effects
        self.debris_manager.draw(self._screen)

        # 4. Control buttons (drawn on top so they are always visible)
        self.exit_button.draw(self._screen)
        self.pause_button.draw(self._screen)

    def _draw_hud(self) -> None:
        """Render Score, Level, and Lives into the top stone HUD banner."""
        hud_x, hud_y, hud_w, hud_h = GAME_HUD_RECT
        center_y = hud_y + hud_h // 2

        # 1. SCORE
        lbl_score = self._hud_lbl_font.render("SCORE:", True, _HUD_TEXT_COLOR)
        val_score = self._hud_val_font.render(f"{self.score:05d}", True, _HUD_TEXT_COLOR)
        score_x = hud_x + int(hud_w * 0.18)
        self._screen.blit(lbl_score, lbl_score.get_rect(center=(score_x, center_y - 18)))
        self._screen.blit(val_score, val_score.get_rect(center=(score_x, center_y + 14)))

        # 2. LEVEL
        lbl_level = self._hud_lbl_font.render("LEVEL", True, _HUD_TEXT_COLOR)
        val_level = self._hud_val_font.render(self.level_str, True, _HUD_TEXT_COLOR)
        level_x = hud_x + int(hud_w * 0.50)
        self._screen.blit(lbl_level, lbl_level.get_rect(center=(level_x, center_y - 18)))
        self._screen.blit(val_level, val_level.get_rect(center=(level_x, center_y + 14)))

        # 3. LIVES
        lbl_lives = self._hud_lbl_font.render("LIVES:", True, _HUD_TEXT_COLOR)
        lives_x = hud_x + int(hud_w * 0.82)
        self._screen.blit(lbl_lives, lbl_lives.get_rect(center=(lives_x, center_y - 18)))

        if (
            self._heart_surf is not None
            and self._heart_dim_surf is not None
            and 0 <= self.lives <= 5
        ):
            # Render a row of hearts: filled for remaining lives, dimmed for lost lives
            gap = 6
            heart_w = self._heart_surf.get_width()
            total_w = self.max_lives * heart_w + (self.max_lives - 1) * gap
            start_x = lives_x - total_w // 2
            for i in range(self.max_lives):
                hx = start_x + i * (heart_w + gap)
                hy = center_y
                surf = self._heart_surf if i < self.lives else self._heart_dim_surf
                self._screen.blit(surf, (hx, hy))
        elif self._heart_surf is not None and self.lives > 5:
            # Fallback for extra high lives count: [heart] x{lives}
            val_lives = self._hud_val_font.render(f"x{self.lives}", True, _HUD_TEXT_COLOR)
            comb_w = self._heart_surf.get_width() + 6 + val_lives.get_width()
            comb_start = lives_x - comb_w // 2
            self._screen.blit(self._heart_surf, (comb_start, center_y))
            self._screen.blit(val_lives, (comb_start + self._heart_surf.get_width() + 6, center_y))
        else:
            val_lives = self._hud_val_font.render(str(self.lives), True, _HUD_TEXT_COLOR)
            self._screen.blit(val_lives, val_lives.get_rect(center=(lives_x, center_y + 14)))
