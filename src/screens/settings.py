"""
src/screens/settings.py
=======================
Settings screen matching the cave-themed mockup.

Layout (800 × 600):
  ┌──────────────────────────────────────────────┐
  │          [ SETTINGS title banner ]            │
  │                                               │
  │     ┌──────────── PANEL ──────────────┐       │
  │     │         AUDIO                   │       │
  │     │  MUSIC VOLUME  ══■════════  ♪   │       │
  │     │  SOUND EFFECTS ══════■════  🔊  │       │
  │     │  ─ ─ ── ─── ── ─── ── ─── ─    │       │
  │     │         CONTROLS                │       │
  │     │  CONTROL MODE                   │       │
  │     │  [KEYBOARD]   [GESTURE]         │       │
  │     │  ─ ─ ── ─── ── ─── ── ─── ─    │       │
  │     └─────────────────────────────────┘       │
  │               [ BACK ]                        │
  └──────────────────────────────────────────────┘
"""

from __future__ import annotations

import os

import pygame

from src.config import (
    FONT_PRIMARY_PATH,
    FONT_SECONDARY_PATH,
    MAIN_MENU_BG_PATH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SFX_CLICK_PATH,
)
from src.core.audio import play_music, play_sfx, stop_music, update_music_volume
from src.core.states import GameState
from src.core.settings import GameSettings

# ---------------------------------------------------------------------------
# Asset paths
# ---------------------------------------------------------------------------
_SETTINGS_UI_DIR = "assets/sprites/ui/settings"
_PANEL_PATH = os.path.join(_SETTINGS_UI_DIR, "panel.png")
_TITLE_PATH = os.path.join(_SETTINGS_UI_DIR, "title_banner.png")
_SLIDER_TRACK_PATH = os.path.join(_SETTINGS_UI_DIR, "slider_track.png")
_SLIDER_KNOB_PATH = os.path.join(_SETTINGS_UI_DIR, "slider_knob.png")
_SEPARATOR_PATH = os.path.join(_SETTINGS_UI_DIR, "separator.png")
_BTN_TOGGLE_ACTIVE_PATH = os.path.join(_SETTINGS_UI_DIR, "btn_toggle_active.png")
_BTN_TOGGLE_INACTIVE_PATH = os.path.join(_SETTINGS_UI_DIR, "btn_toggle_inactive.png")
_BTN_BACK_PATH = os.path.join(_SETTINGS_UI_DIR, "btn_back_large.png")

# ---------------------------------------------------------------------------
# Layout constants (800 × 600 logical)
# ---------------------------------------------------------------------------
_TEXT_COLOR = (66, 19, 14)
_TEXT_COLOR_HOVER = (135, 36, 26)
_SECTION_COLOR = (120, 30, 25)

# Panel
_PANEL_W = 440
_PANEL_H = 380
_PANEL_X = (SCREEN_WIDTH - _PANEL_W) // 2
_PANEL_Y = 140

# Title banner
_TITLE_W = 360
_TITLE_H = 80
_TITLE_X = (SCREEN_WIDTH - _TITLE_W) // 2
_TITLE_Y = 44

# Slider geometry (inside panel)
_SLIDER_LABEL_X = _PANEL_X + 30
_SLIDER_TRACK_X = _PANEL_X + 195
_SLIDER_TRACK_W = 190
_SLIDER_TRACK_H = 22
_SLIDER_KNOB_W = 30
_SLIDER_KNOB_H = 22
_MUSIC_SLIDER_Y = _PANEL_Y + 80
_SFX_SLIDER_Y = _PANEL_Y + 120

# Separator
_SEP_W = _PANEL_W - 50
_SEP_X = _PANEL_X + 25
_SEP1_Y = _PANEL_Y + 160
_SEP2_Y = _PANEL_Y + 310

# Controls section
_CONTROLS_LABEL_Y = _PANEL_Y + 178
_CTRL_MODE_LABEL_Y = _PANEL_Y + 210
_CTRL_BTN_Y = _PANEL_Y + 240
_CTRL_BTN_W = 140
_CTRL_BTN_H = 55
_CTRL_BTN_GAP = 20
_CTRL_BTN_X_LEFT = (SCREEN_WIDTH - 2 * _CTRL_BTN_W - _CTRL_BTN_GAP) // 2
_CTRL_BTN_X_RIGHT = _CTRL_BTN_X_LEFT + _CTRL_BTN_W + _CTRL_BTN_GAP

# Back button
_BACK_W = 180
_BACK_H = 65
_BACK_X = (SCREEN_WIDTH - _BACK_W) // 2
_BACK_Y = _PANEL_Y + _PANEL_H + 20


def _load_scaled(path: str, size: tuple[int, int]) -> pygame.Surface | None:
    if not os.path.exists(path):
        return None
    raw = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(raw, size)


class _VolumeSlider:
    """Draggable volume slider widget."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        value: float,
        track_surf: pygame.Surface | None,
        knob_surf: pygame.Surface | None,
    ) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.value = value  # 0.0 – 1.0
        self._track_surf = track_surf
        self._knob_surf = knob_surf
        self._dragging = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    @property
    def knob_rect(self) -> pygame.Rect:
        kx = self.x + int(self.value * (self.width - _SLIDER_KNOB_W))
        return pygame.Rect(kx, self.y - 1, _SLIDER_KNOB_W, self.height + 2)

    def handle_event(self, ev: pygame.event.Event) -> bool:
        """Returns True if value changed."""
        changed = False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            # Click on knob or track
            expanded = self.rect.inflate(10, 20)
            if expanded.collidepoint(ev.pos):
                self._dragging = True
                changed = self._update_from_mouse(ev.pos[0])
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self._dragging:
                self._dragging = False
        elif ev.type == pygame.MOUSEMOTION:
            if self._dragging:
                changed = self._update_from_mouse(ev.pos[0])
        return changed

    def _update_from_mouse(self, mx: int) -> bool:
        old = self.value
        raw = (mx - self.x) / max(1, self.width - _SLIDER_KNOB_W)
        self.value = max(0.0, min(1.0, raw))
        # Snap to 0.05 increments
        self.value = round(self.value * 20) / 20
        return abs(self.value - old) > 0.001

    def draw(self, surface: pygame.Surface) -> None:
        # Track
        if self._track_surf is not None:
            surface.blit(self._track_surf, (self.x, self.y))
        else:
            pygame.draw.rect(surface, (80, 50, 40), self.rect, border_radius=4)
            inner = pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4)
            pygame.draw.rect(surface, (140, 100, 80), inner, border_radius=3)

        # Filled portion
        fill_w = int(self.value * (self.width - _SLIDER_KNOB_W)) + _SLIDER_KNOB_W // 2
        fill_rect = pygame.Rect(self.x + 3, self.y + 3, fill_w - 3, self.height - 6)
        fill_surf = pygame.Surface(fill_rect.size, pygame.SRCALPHA)
        fill_surf.fill((160, 80, 60, 80))
        surface.blit(fill_surf, fill_rect.topleft)

        # Knob
        kr = self.knob_rect
        if self._knob_surf is not None:
            surface.blit(self._knob_surf, kr.topleft)
        else:
            pygame.draw.rect(surface, (100, 60, 50), kr, border_radius=4)
            pygame.draw.rect(surface, (60, 30, 25), kr, 2, border_radius=4)


class SettingsMenu:
    """Settings menu screen with volume sliders and control mode toggles."""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._next_state: GameState | None = None

        # ── Background ────────────────────────────────────────────────────
        self._bg: pygame.Surface
        if os.path.exists(MAIN_MENU_BG_PATH):
            raw_bg = pygame.image.load(MAIN_MENU_BG_PATH).convert()
            if raw_bg.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
                self._bg = pygame.transform.smoothscale(
                    raw_bg, (SCREEN_WIDTH, SCREEN_HEIGHT)
                )
            else:
                self._bg = raw_bg
        else:
            self._bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self._bg.fill((35, 25, 30))

        # ── Fonts ─────────────────────────────────────────────────────────
        font_path = None
        if os.path.exists(FONT_PRIMARY_PATH):
            font_path = FONT_PRIMARY_PATH
        elif os.path.exists(FONT_SECONDARY_PATH):
            font_path = FONT_SECONDARY_PATH

        self._section_font = pygame.font.Font(font_path, 30)
        self._label_font = pygame.font.Font(font_path, 20)
        self._btn_font = pygame.font.Font(font_path, 24)
        self._back_font = pygame.font.Font(font_path, 32)

        # ── Sprites ───────────────────────────────────────────────────────
        self._panel_surf = _load_scaled(_PANEL_PATH, (_PANEL_W, _PANEL_H))
        self._title_surf = _load_scaled(_TITLE_PATH, (_TITLE_W, _TITLE_H))
        self._separator_surf = _load_scaled(_SEPARATOR_PATH, (_SEP_W, 6))
        self._back_surf = _load_scaled(_BTN_BACK_PATH, (_BACK_W, _BACK_H))

        slider_track_surf = _load_scaled(
            _SLIDER_TRACK_PATH, (_SLIDER_TRACK_W, _SLIDER_TRACK_H)
        )
        slider_knob_surf = _load_scaled(
            _SLIDER_KNOB_PATH, (_SLIDER_KNOB_W, _SLIDER_KNOB_H)
        )

        self._btn_active_surf = _load_scaled(
            _BTN_TOGGLE_ACTIVE_PATH, (_CTRL_BTN_W, _CTRL_BTN_H)
        )
        self._btn_inactive_surf = _load_scaled(
            _BTN_TOGGLE_INACTIVE_PATH, (_CTRL_BTN_W, _CTRL_BTN_H)
        )

        # Back button hover surface
        self._back_hover_surf: pygame.Surface | None = None
        if self._back_surf is not None:
            self._back_hover_surf = self._back_surf.copy()
            tint = pygame.Surface((_BACK_W, _BACK_H), pygame.SRCALPHA)
            tint.fill((255, 255, 220, 32))
            self._back_hover_surf.blit(tint, (0, 0))

        # ── Sliders ───────────────────────────────────────────────────────
        self._music_slider = _VolumeSlider(
            _SLIDER_TRACK_X,
            _MUSIC_SLIDER_Y,
            _SLIDER_TRACK_W,
            _SLIDER_TRACK_H,
            GameSettings.music_volume,
            slider_track_surf,
            slider_knob_surf,
        )
        self._sfx_slider = _VolumeSlider(
            _SLIDER_TRACK_X,
            _SFX_SLIDER_Y,
            _SLIDER_TRACK_W,
            _SLIDER_TRACK_H,
            GameSettings.sfx_volume,
            slider_track_surf,
            slider_knob_surf,
        )

        # ── Control mode toggle rects ─────────────────────────────────────
        self._kb_rect = pygame.Rect(
            _CTRL_BTN_X_LEFT, _CTRL_BTN_Y, _CTRL_BTN_W, _CTRL_BTN_H
        )
        self._gesture_rect = pygame.Rect(
            _CTRL_BTN_X_RIGHT, _CTRL_BTN_Y, _CTRL_BTN_W, _CTRL_BTN_H
        )

        # Back button rect
        self._back_rect = pygame.Rect(_BACK_X, _BACK_Y, _BACK_W, _BACK_H)
        self._back_hovered = False

    # ------------------------------------------------------------------
    # State interface
    # ------------------------------------------------------------------

    def reset_state(self) -> None:
        self._next_state = None
        self._music_slider.value = GameSettings.music_volume
        self._sfx_slider.value = GameSettings.sfx_volume

    @property
    def next_state(self) -> GameState | None:
        return self._next_state

    # ------------------------------------------------------------------
    # Game-loop
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for ev in events:
            # Sliders
            if self._music_slider.handle_event(ev):
                GameSettings.music_volume = self._music_slider.value
                update_music_volume()
                GameSettings.save()

            if self._sfx_slider.handle_event(ev):
                GameSettings.sfx_volume = self._sfx_slider.value
                GameSettings.save()

            # Mouse interactions
            if ev.type == pygame.MOUSEMOTION:
                self._back_hovered = self._back_rect.collidepoint(ev.pos)

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pos = ev.pos
                # Control mode toggle
                if self._kb_rect.collidepoint(pos):
                    GameSettings.control_mode = "keyboard"
                    play_sfx(SFX_CLICK_PATH)
                    GameSettings.save()
                elif self._gesture_rect.collidepoint(pos):
                    GameSettings.control_mode = "gesture"
                    play_sfx(SFX_CLICK_PATH)
                    GameSettings.save()

            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                pos = ev.pos
                if self._back_rect.collidepoint(pos):
                    play_sfx(SFX_CLICK_PATH)
                    self._next_state = GameState.MAIN_MENU

            # Keyboard
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self._next_state = GameState.MAIN_MENU

    def update(self, dt: float) -> None:
        del dt

    def draw(self) -> None:
        # 1. Background
        self._screen.blit(self._bg, (0, 0))

        # 2. Title banner
        if self._title_surf is not None:
            self._screen.blit(self._title_surf, (_TITLE_X, _TITLE_Y))
        # Draw "SETTINGS" text on the title banner
        title_text = self._section_font.render("SETTINGS", True, _SECTION_COLOR)
        title_text_rect = title_text.get_rect(
            center=(_TITLE_X + _TITLE_W // 2, _TITLE_Y + _TITLE_H // 2 + 8)
        )
        self._screen.blit(title_text, title_text_rect)

        # 3. Panel
        if self._panel_surf is not None:
            self._screen.blit(self._panel_surf, (_PANEL_X, _PANEL_Y))

        # 4. AUDIO section
        audio_header = self._section_font.render("AUDIO", True, _SECTION_COLOR)
        self._screen.blit(
            audio_header,
            audio_header.get_rect(
                center=(_PANEL_X + _PANEL_W // 2, _PANEL_Y + 45)
            ),
        )

        # Music Volume label + slider
        music_lbl = self._label_font.render("MUSIC VOLUME", True, _TEXT_COLOR)
        self._screen.blit(music_lbl, (_SLIDER_LABEL_X, _MUSIC_SLIDER_Y + 2))
        self._music_slider.draw(self._screen)
        # Music note icon text
        note_text = self._label_font.render("♪", True, _TEXT_COLOR)
        self._screen.blit(
            note_text,
            (_SLIDER_TRACK_X + _SLIDER_TRACK_W + 10, _MUSIC_SLIDER_Y + 1),
        )

        # SFX Volume label + slider
        sfx_lbl = self._label_font.render("SOUND EFFECTS", True, _TEXT_COLOR)
        self._screen.blit(sfx_lbl, (_SLIDER_LABEL_X, _SFX_SLIDER_Y + 2))
        self._sfx_slider.draw(self._screen)
        # Speaker icon text
        spk_text = self._label_font.render("🔊", True, _TEXT_COLOR)
        self._screen.blit(
            spk_text,
            (_SLIDER_TRACK_X + _SLIDER_TRACK_W + 10, _SFX_SLIDER_Y + 1),
        )

        # 5. Separator 1
        if self._separator_surf is not None:
            self._screen.blit(self._separator_surf, (_SEP_X, _SEP1_Y))

        # 6. CONTROLS section
        ctrl_header = self._section_font.render("CONTROLS", True, _SECTION_COLOR)
        self._screen.blit(
            ctrl_header,
            ctrl_header.get_rect(
                center=(_PANEL_X + _PANEL_W // 2, _CONTROLS_LABEL_Y)
            ),
        )

        mode_lbl = self._label_font.render("CONTROL MODE", True, _TEXT_COLOR)
        self._screen.blit(
            mode_lbl,
            mode_lbl.get_rect(
                center=(_PANEL_X + _PANEL_W // 2, _CTRL_MODE_LABEL_Y)
            ),
        )

        # Keyboard toggle button
        is_kb = GameSettings.control_mode == "keyboard"
        kb_surf = self._btn_active_surf if is_kb else self._btn_inactive_surf
        if kb_surf is not None:
            self._screen.blit(kb_surf, self._kb_rect.topleft)
        kb_text = self._btn_font.render("KEYBOARD", True, (255, 255, 255) if is_kb else _TEXT_COLOR)
        self._screen.blit(
            kb_text, kb_text.get_rect(center=self._kb_rect.center)
        )

        # Gesture toggle button
        is_gs = GameSettings.control_mode == "gesture"
        gs_surf = self._btn_active_surf if is_gs else self._btn_inactive_surf
        if gs_surf is not None:
            self._screen.blit(gs_surf, self._gesture_rect.topleft)
        gs_text = self._btn_font.render("GESTURE", True, (255, 255, 255) if is_gs else _TEXT_COLOR)
        self._screen.blit(
            gs_text, gs_text.get_rect(center=self._gesture_rect.center)
        )

        # 7. Separator 2
        if self._separator_surf is not None:
            self._screen.blit(self._separator_surf, (_SEP_X, _SEP2_Y))

        # 8. BACK button
        back_surf = self._back_hover_surf if self._back_hovered else self._back_surf
        if back_surf is not None:
            self._screen.blit(back_surf, self._back_rect.topleft)
        else:
            pygame.draw.rect(self._screen, (100, 60, 40), self._back_rect, border_radius=6)

        # The back button sprite already has "BACK" baked in, so skip text
        # unless the sprite is missing.
        if back_surf is None:
            back_text = self._back_font.render("BACK", True, _TEXT_COLOR)
            self._screen.blit(
                back_text, back_text.get_rect(center=self._back_rect.center)
            )
