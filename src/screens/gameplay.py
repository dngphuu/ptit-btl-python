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
from src.core.audio import play_music, stop_music, play_sfx
from src.core.states import GameState
from src.entities import Brick, BrickGrid, BrickRenderer, Playfield, Paddle, Ball
from src.ui.button import MenuButton
import cv2
import numpy as np
from src.vision.camera import CameraPipeline
from src.vision.input_processor import InputProcessor
from src.config import SFX_LEVEL_COMPLETE_PATH, SFX_LEVEL_FAIL_PATH

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
        self.level: int = 1
        self.lives: int = 3
        self.high_score: int = self._load_high_score()

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
        
        self.paddle: Paddle = Paddle(self.playfield)
        self.ball: Ball = Ball(self.playfield, self.paddle)

        from src.entities.debris import DebrisManager
        self.debris_manager: DebrisManager = DebrisManager()
        
        self.ball.set_difficulty(self.level)

        # Vision pipeline
        self.camera_pipeline = CameraPipeline()
        self.input_processor = InputProcessor()
        self.camera_pipeline.start()
        self.latest_frame = None
        self.landmark = None

    def _load_high_score(self) -> int:
        try:
            if os.path.exists("highscore.txt"):
                with open("highscore.txt", "r") as f:
                    return int(f.read().strip())
        except Exception:
            pass
        return 0
        
    def _save_high_score(self) -> None:
        try:
            with open("highscore.txt", "w") as f:
                f.write(str(self.high_score))
        except Exception:
            pass

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
        self.score = 0
        self.level = 1
        self.lives = 3
        self.paddle.x = self.playfield.center_x
        self.ball.set_difficulty(self.level)
        self.ball.reset()

    @property
    def is_paused(self) -> bool:
        """Whether gameplay is currently paused."""
        return self._is_paused

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        self._is_paused = not self._is_paused
        if pygame.mixer.get_init():
            if self._is_paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

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
            self._save_high_score()
            if self._is_paused:
                self.toggle_pause()
            self._next_state = GameState.MAIN_MENU

        # Pause button click -> toggle pause
        if self.pause_button.update(events):
            self.toggle_pause()

        # Keyboard fallback navigation
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self._save_high_score()
                    if self._is_paused:
                        self.toggle_pause()
                    self._next_state = GameState.MAIN_MENU
                elif ev.key == pygame.K_p:
                    self.toggle_pause()

    def update(self, dt: float) -> None:
        """Advance gameplay logic and animations."""
        if self._is_paused:
            return
            
        keys = pygame.key.get_pressed()
        
        # Process vision input
        frame = self.camera_pipeline.read()
        if frame is not None:
            landmark = self.input_processor.process(frame, flip_horizontal=False)
            self.landmark = landmark
            if landmark:
                InputProcessor.draw_landmarks(frame, landmark)
                # Map landmark x [0,1] to paddle x
                target_x = self.playfield.rect.x + landmark.x * self.playfield.rect.width
                # Smoothly move or just snap. Let's snap for immediate response.
                self.paddle.x = target_x
                
                # Check for closed hand gesture to launch ball
                if not self.ball.active and landmark.raw_landmarks:
                    lm = landmark.raw_landmarks
                    def dist(p1, p2):
                        return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
                    closed = True
                    for mcp_idx, tip_idx in [(5, 8), (9, 12), (13, 16), (17, 20)]:
                        if dist(lm[tip_idx], lm[0]) > dist(lm[mcp_idx], lm[0]):
                            closed = False
                            break
                    if closed:
                        import math
                        self.ball.active = True
                        self.ball.current_speed = self.ball.base_speed
                        length = math.hypot(self.ball.vx, self.ball.vy)
                        if length != 0:
                            self.ball.vx = (self.ball.vx / length) * self.ball.current_speed
                            self.ball.vy = (self.ball.vy / length) * self.ball.current_speed
            
            self.latest_frame = frame
            
        self.paddle.update(keys, dt)
        
        was_active = self.ball.active
        points_earned = self.ball.update(dt, keys, self.brick_grid)
        self.score += points_earned
        
        if self.score > self.high_score:
            self.high_score = self.score
        
        # Check level complete
        if len(self.brick_grid.alive_bricks()) == 0:
            self.score += int(500 * self.ball.score_multiplier)  # Level clear bonus
            if self.score > self.high_score:
                self.high_score = self.score
                
            play_sfx(SFX_LEVEL_COMPLETE_PATH)
            self.level += 1
            self.ball.set_difficulty(self.level)
            self.brick_grid.reset()
            self.paddle.x = self.playfield.center_x
            self.ball.reset()
        
        # Check if ball fell out (it becomes inactive after falling out)
        if was_active and not self.ball.active:
            self.lives -= 1
            if self.lives <= 0:
                play_sfx(SFX_LEVEL_FAIL_PATH)
                self._save_high_score()
                self._next_state = GameState.MAIN_MENU
                self.reset_state()
                
        self.debris_manager.update()

    def draw(self) -> None:
        """Render frame background, HUD panel contents, and UI buttons."""
        # 1. Background frame
        self._screen.blit(self._bg, (0, 0))
        
        # 1.5 Camera feed
        if self.latest_frame is not None:
            frame_rgb = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)
            frame_surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            cam_w, cam_h = 160, 120
            frame_surf = pygame.transform.smoothscale(frame_surf, (cam_w, cam_h))
            self._screen.blit(frame_surf, (SCREEN_WIDTH - cam_w - 20, 80))

        # 2. Top HUD banner text
        self._draw_hud()

        # 3. Brick grid (drawn via BrickRenderer)
        self.brick_renderer.render(self._screen, self.brick_grid)
        
        # 3.2. Paddle and Ball
        self.paddle.draw(self._screen)
        self.ball.draw(self._screen)
        
        # 3.5. Debris effects
        self.debris_manager.draw(self._screen)

        # 4. Control buttons (drawn on top so they are always visible)
        self.exit_button.draw(self._screen)
        self.pause_button.draw(self._screen)

        if self._is_paused:
            self._draw_pause_overlay()

    def _draw_pause_overlay(self) -> None:
        """Render a dimming overlay and 'PAUSED' text."""
        overlay = pygame.Surface(self._screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self._screen.blit(overlay, (0, 0))

        # Use the same font path as the HUD but larger
        font_path = None
        if os.path.exists(FONT_SECONDARY_PATH):
            font_path = FONT_SECONDARY_PATH
        elif os.path.exists(FONT_PRIMARY_PATH):
            font_path = FONT_PRIMARY_PATH

        font = pygame.font.Font(font_path, 72)
        text = font.render("PAUSED", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self._screen.get_width() // 2, self._screen.get_height() // 2 - 30))
        self._screen.blit(text, text_rect)

        small_font = pygame.font.Font(font_path, 24)
        sub_text = small_font.render("Press P or PAUSE button to resume", True, (200, 200, 200))
        sub_text_rect = sub_text.get_rect(center=(self._screen.get_width() // 2, self._screen.get_height() // 2 + 30))
        self._screen.blit(sub_text, sub_text_rect)

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

        # 2. HI-SCORE
        lbl_level = self._hud_lbl_font.render("HI-SCORE", True, _HUD_TEXT_COLOR)
        val_level = self._hud_val_font.render(f"{self.high_score:05d}", True, _HUD_TEXT_COLOR)
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
            # Render a row of hearts: filled for remaining lives, hidden for lost lives
            gap = 6
            heart_w = self._heart_surf.get_width()
            total_w = self.max_lives * heart_w + (self.max_lives - 1) * gap
            start_x = lives_x - total_w // 2
            for i in range(self.max_lives):
                if i < self.lives:
                    hx = start_x + i * (heart_w + gap)
                    hy = center_y
                    self._screen.blit(self._heart_surf, (hx, hy))
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
