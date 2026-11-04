"""
src/screens/settings.py
=======================
Settings screen matching the cave-themed mockup design (mockups/settings_menu.png).

Layout (800 x 600 logical resolution):
  - Cave background with glowing mushrooms, crystals, and lantern.
  - Centered stone & parchment plaque dialog box with corner brackets.
  - "SETTINGS" title header plaque mounted over the top border.
  - "GESTURE CONTROL" label with pixel-art [ ON | OFF ] toggle switch button.
  - "VOLUME" label with slider bar and speaker icon.
  - "BACK" stone button at the bottom.
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
    SETTINGS_UI_DIR,
    SFX_CLICK_PATH,
)
from src.core.audio import play_sfx, set_music_volume
from src.core.settings import GameSettings
from src.core.states import GameState

# ---------------------------------------------------------------------------
# Asset paths
# ---------------------------------------------------------------------------
_SETTINGS_UI_DIR = SETTINGS_UI_DIR
_BASE_BG_PATH = os.path.join(_SETTINGS_UI_DIR, "settings_menu_base.png")
_BTN_TOGGLE_ON_PATH = os.path.join(_SETTINGS_UI_DIR, "btn_toggle_on.png")
_BTN_TOGGLE_OFF_PATH = os.path.join(_SETTINGS_UI_DIR, "btn_toggle_off.png")
_SLIDER_TRACK_PATH = os.path.join(_SETTINGS_UI_DIR, "slider_track.png")
_SLIDER_KNOB_PATH = os.path.join(_SETTINGS_UI_DIR, "slider_knob.png")
_SLIDER_FILL_PATH = os.path.join(_SETTINGS_UI_DIR, "slider_fill.png")

# ---------------------------------------------------------------------------
# Layout coordinates (800 x 600 logical resolution)
# ---------------------------------------------------------------------------
_TOGGLE_RECT = pygame.Rect(417, 207, 178, 64)
_SLIDER_RECT = pygame.Rect(377, 298, 189, 44)
_SLIDER_MIN_X = 390
_SLIDER_MAX_X = 552
_SLIDER_CENTER_Y = 319
_SPEAKER_RECT = pygame.Rect(572, 304, 35, 32)
_BACK_RECT = pygame.Rect(304, 369, 202, 72)

_TEXT_COLOR = (66, 19, 14)
_TEXT_COLOR_HOVER = (135, 36, 26)


def _load_image(path: str, size: tuple[int, int] | None = None) -> pygame.Surface | None:
    """Helper to safely load and scale an image."""
    if not os.path.exists(path):
        return None
    try:
        surf = pygame.image.load(path)
        try:
            surf = surf.convert_alpha() if surf.get_masks()[3] != 0 else surf.convert()
        except Exception:
            pass
        if size is not None and surf.get_size() != size:
            surf = pygame.transform.smoothscale(surf, size)
        return surf
    except Exception:
        return None


class GestureToggleButton:
    """Interactive pixel-art toggle switch button for Gesture Control."""

    def __init__(
        self,
        rect: pygame.Rect,
        surf_on: pygame.Surface | None,
        surf_off: pygame.Surface | None,
    ) -> None:
        self.rect = rect
        self._surf_on = surf_on
        self._surf_off = surf_off
        self.is_hovered: bool = False
        self.is_focused: bool = False

        # Precompute hover overlays
        self._hover_overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            self._hover_overlay,
            (255, 255, 255, 35),
            self._hover_overlay.get_rect(),
            border_radius=6,
        )

        self._focus_overlay = pygame.Surface(
            (self.rect.width + 6, self.rect.height + 6), pygame.SRCALPHA
        )
        pygame.draw.rect(
            self._focus_overlay,
            (240, 200, 120, 160),
            self._focus_overlay.get_rect(),
            2,
            border_radius=6,
        )

    def is_on(self) -> bool:
        return GameSettings.is_gesture_on()

    def toggle(self) -> None:
        """Flip the toggle state, play SFX, and persist settings."""
        new_val = not self.is_on()
        GameSettings.set_gesture_control(new_val)
        play_sfx(SFX_CLICK_PATH)

    def set_state(self, enabled: bool) -> None:
        if self.is_on() != enabled:
            GameSettings.set_gesture_control(enabled)
            play_sfx(SFX_CLICK_PATH)

    def handle_event(self, ev: pygame.event.Event) -> bool:
        """Handle mouse and keyboard events. Returns True if state changed."""
        if ev.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(ev.pos)
            return False

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                # Clicking the left half directly selects ON, right half selects OFF
                half_w = self.rect.width // 2
                if ev.pos[0] < self.rect.x + half_w:
                    self.set_state(True)
                else:
                    self.set_state(False)
                return True

        if ev.type == pygame.KEYDOWN and self.is_focused:
            if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.toggle()
                return True
            elif ev.key in (pygame.K_LEFT, pygame.K_a):
                self.set_state(True)
                return True
            elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                self.set_state(False)
                return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        surf = self._surf_on if self.is_on() else self._surf_off
        if surf is not None:
            surface.blit(surf, self.rect.topleft)
        else:
            # Procedural fallback
            bg_col = (70, 130, 80) if self.is_on() else (140, 50, 50)
            pygame.draw.rect(surface, bg_col, self.rect, border_radius=6)
            pygame.draw.rect(surface, (50, 40, 40), self.rect, 3, border_radius=6)

        # Hover highlight
        if self.is_hovered:
            surface.blit(self._hover_overlay, self.rect.topleft)

        # Keyboard focus indicator
        if self.is_focused:
            surface.blit(self._focus_overlay, (self.rect.x - 3, self.rect.y - 3))


class VolumeSlider:
    """
    Interactive pixel-art volume slider widget matching the cave-themed aesthetic.
    Supports dragging, clicking along the track, speaker mute toggle, and keyboard navigation.
    """

    def __init__(
        self,
        rect: pygame.Rect = _SLIDER_RECT,
        knob_surf: pygame.Surface | None = None,
        fill_surf: pygame.Surface | None = None,
        track_surf: pygame.Surface | None = None,
        speaker_rect: pygame.Rect = _SPEAKER_RECT,
    ) -> None:
        self.rect = rect
        self._knob_surf = knob_surf
        self._fill_surf = fill_surf
        self._track_surf = track_surf
        self._speaker_rect = speaker_rect

        self.min_x: int = _SLIDER_MIN_X
        self.max_x: int = _SLIDER_MAX_X
        self.center_y: int = _SLIDER_CENTER_Y
        self.travel: int = max(1, self.max_x - self.min_x)

        self._dragging: bool = False
        self.is_hovered: bool = False
        self.is_focused: bool = False
        self._last_unmuted_volume: float = 0.5

        # Knob dimensions
        self.knob_width: int = 24 if self._knob_surf is None else self._knob_surf.get_width()
        self.knob_height: int = 44 if self._knob_surf is None else self._knob_surf.get_height()

        # Hover & Focus overlays
        self._knob_hover_overlay = pygame.Surface(
            (self.knob_width, self.knob_height), pygame.SRCALPHA
        )
        self._knob_hover_overlay.fill((255, 255, 255, 45))

        # Focus overlay around slider track
        self._focus_overlay = pygame.Surface(
            (self.rect.width + 10, self.rect.height + 8), pygame.SRCALPHA
        )
        pygame.draw.rect(
            self._focus_overlay,
            (240, 200, 120, 160),
            self._focus_overlay.get_rect(),
            2,
            border_radius=6,
        )

        # Mute indicator (subtle red cross for speaker icon when muted)
        self._mute_overlay = pygame.Surface(self._speaker_rect.size, pygame.SRCALPHA)
        pygame.draw.line(
            self._mute_overlay,
            (210, 50, 50, 220),
            (6, 6),
            (self._speaker_rect.width - 6, self._speaker_rect.height - 6),
            3,
        )
        pygame.draw.line(
            self._mute_overlay,
            (210, 50, 50, 220),
            (6, self._speaker_rect.height - 6),
            (self._speaker_rect.width - 6, 6),
            3,
        )

    @property
    def value(self) -> float:
        return GameSettings.get_volume()

    def set_value(self, val: float, play_sound: bool = False) -> None:
        new_val = max(0.0, min(1.0, round(float(val), 2)))
        if abs(new_val - self.value) > 0.001:
            if new_val > 0.0:
                self._last_unmuted_volume = new_val
            GameSettings.set_volume(new_val)
            set_music_volume(new_val)
            if play_sound:
                play_sfx(SFX_CLICK_PATH)

    def toggle_mute(self) -> None:
        if self.value > 0.0:
            self._last_unmuted_volume = self.value
            self.set_value(0.0, play_sound=True)
        else:
            restore_vol = self._last_unmuted_volume if self._last_unmuted_volume > 0.0 else 0.5
            self.set_value(restore_vol, play_sound=True)

    @property
    def knob_center_x(self) -> int:
        return self.min_x + int(self.value * self.travel)

    @property
    def knob_rect(self) -> pygame.Rect:
        kx = self.knob_center_x
        return pygame.Rect(
            kx - self.knob_width // 2,
            self.center_y - self.knob_height // 2,
            self.knob_width,
            self.knob_height,
        )

    def _val_from_mouse_x(self, mx: int) -> float:
        raw = (mx - self.min_x) / float(self.travel)
        return max(0.0, min(1.0, round(raw, 2)))

    def handle_event(self, ev: pygame.event.Event) -> bool:
        """Handle mouse motion, drag, click, and keyboard events."""
        if ev.type == pygame.MOUSEMOTION:
            slider_hit = self.rect.inflate(14, 14).collidepoint(ev.pos)
            speaker_hit = self._speaker_rect.collidepoint(ev.pos)
            self.is_hovered = slider_hit or speaker_hit

            if self._dragging:
                new_val = self._val_from_mouse_x(ev.pos[0])
                if abs(new_val - self.value) > 0.001:
                    self.set_value(new_val)
                    return True
            return False

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            # Check speaker click (mute toggle)
            if self._speaker_rect.collidepoint(ev.pos):
                self.toggle_mute()
                return True

            # Check slider track/knob click (start drag)
            if self.rect.inflate(14, 14).collidepoint(ev.pos):
                self._dragging = True
                new_val = self._val_from_mouse_x(ev.pos[0])
                self.set_value(new_val, play_sound=True)
                return True

        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self._dragging:
                self._dragging = False
                GameSettings.save()
                return True

        if ev.type == pygame.KEYDOWN and self.is_focused:
            if ev.key in (pygame.K_LEFT, pygame.K_a):
                self.set_value(self.value - 0.05, play_sound=True)
                return True
            elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                self.set_value(self.value + 0.05, play_sound=True)
                return True
            elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_m):
                self.toggle_mute()
                return True
            elif ev.key == pygame.K_HOME:
                self.set_value(0.0, play_sound=True)
                return True
            elif ev.key == pygame.K_END:
                self.set_value(1.0, play_sound=True)
                return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Render the volume slider (track overlay, fill segments, knob, and indicators)."""
        # Optional: draw base track if supplied
        if self._track_surf is not None:
            surface.blit(self._track_surf, (self.rect.x, 303))

        # 1. Filled groove segments
        kx = self.knob_center_x
        fill_w = kx - self.min_x
        if fill_w > 0:
            if self._fill_surf is not None:
                max_w = min(self._fill_surf.get_width(), fill_w)
                surface.blit(
                    self._fill_surf.subsurface((0, 0, max_w, 15)),
                    (self.min_x, 312),
                )
            else:
                # Fallback filled color
                pygame.draw.rect(
                    surface,
                    (130, 110, 115),
                    (self.min_x, 312, fill_w, 15),
                    border_radius=2,
                )

        # 2. Knob
        k_rect = self.knob_rect
        if self._knob_surf is not None:
            surface.blit(self._knob_surf, k_rect.topleft)
        else:
            pygame.draw.rect(surface, (140, 120, 130), k_rect, border_radius=4)
            pygame.draw.rect(surface, (45, 30, 35), k_rect, 2, border_radius=4)

        # Hover highlight on knob
        if self.is_hovered or self._dragging:
            surface.blit(self._knob_hover_overlay, k_rect.topleft)

        # Keyboard focus indicator around slider track
        if self.is_focused:
            surface.blit(
                self._focus_overlay,
                (self.rect.x - 5, self.rect.y - 4),
            )

        # Mute indicator on speaker if volume is 0
        if self.value <= 0.0:
            surface.blit(self._mute_overlay, self._speaker_rect.topleft)


class SettingsMenu:
    """
    Settings menu screen matching mockups/settings_menu.png.

    Features:
      - Complete main layout matching the cave aesthetic.
      - Interactive ON/OFF toggle switch button for Gesture Control.
      - Interactive Volume Slider with drag, click-to-position, and mute toggle.
      - Seamless integration with GameSettings and persistence to settings.json.
      - Interactive BACK button returning to MAIN_MENU.
      - Full mouse and keyboard navigation support.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._next_state: GameState | None = None

        # ── Base Layout Background ────────────────────────────────────────
        self._base_surf: pygame.Surface | None = _load_image(
            _BASE_BG_PATH, (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        if self._base_surf is None:
            # Fallback to main menu cave bg if custom base doesn't exist
            self._base_surf = _load_image(MAIN_MENU_BG_PATH, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # ── Toggle Button Sprites ─────────────────────────────────────────
        toggle_on_surf = _load_image(_BTN_TOGGLE_ON_PATH, (_TOGGLE_RECT.width, _TOGGLE_RECT.height))
        toggle_off_surf = _load_image(
            _BTN_TOGGLE_OFF_PATH, (_TOGGLE_RECT.width, _TOGGLE_RECT.height)
        )

        self._toggle_btn = GestureToggleButton(_TOGGLE_RECT, toggle_on_surf, toggle_off_surf)

        # ── Volume Slider Sprites ─────────────────────────────────────────
        knob_surf = _load_image(_SLIDER_KNOB_PATH)
        fill_surf = _load_image(_SLIDER_FILL_PATH)
        track_surf = _load_image(_SLIDER_TRACK_PATH)

        self._volume_slider = VolumeSlider(
            rect=_SLIDER_RECT,
            knob_surf=knob_surf,
            fill_surf=fill_surf,
            track_surf=track_surf,
            speaker_rect=_SPEAKER_RECT,
        )

        # ── Back Button ───────────────────────────────────────────────────
        self._back_rect = _BACK_RECT
        self._back_hovered = False
        self._back_focused = False

        # Back button hover & focus overlays
        self._back_hover_overlay = pygame.Surface(self._back_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            self._back_hover_overlay,
            (255, 255, 200, 35),
            self._back_hover_overlay.get_rect(),
            border_radius=4,
        )
        pygame.draw.rect(
            self._back_hover_overlay,
            (255, 230, 160, 140),
            self._back_hover_overlay.get_rect(),
            2,
            border_radius=4,
        )

        self._back_focus_overlay = pygame.Surface(
            (self._back_rect.width + 6, self._back_rect.height + 6), pygame.SRCALPHA
        )
        pygame.draw.rect(
            self._back_focus_overlay,
            (240, 200, 120, 160),
            self._back_focus_overlay.get_rect(),
            2,
            border_radius=6,
        )

        # ── Focus management for keyboard navigation ──────────────────────
        # 0: Gesture Toggle, 1: Volume Slider, 2: Back Button
        self._focus_index: int = -1

        # ── Fonts ─────────────────────────────────────────────────────────
        font_path = (
            FONT_PRIMARY_PATH
            if os.path.exists(FONT_PRIMARY_PATH)
            else (FONT_SECONDARY_PATH if os.path.exists(FONT_SECONDARY_PATH) else None)
        )
        self._font = pygame.font.Font(font_path, 28)

    # ------------------------------------------------------------------
    # State interface
    # ------------------------------------------------------------------

    def reset_state(self) -> None:
        """Reset internal navigation state upon entering the screen."""
        self._next_state = None
        self._focus_index = -1
        self._back_hovered = False
        self._toggle_btn.is_hovered = False
        self._toggle_btn.is_focused = False
        self._volume_slider.is_hovered = False
        self._volume_slider.is_focused = False
        self._volume_slider._dragging = False
        self._back_focused = False
        GameSettings.load()

    @property
    def next_state(self) -> GameState | None:
        """Next GameState requested by user interaction, or None."""
        return self._next_state

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for ev in events:
            # Mouse motion: check hovers and update cursor
            if ev.type == pygame.MOUSEMOTION:
                self._toggle_btn.handle_event(ev)
                self._volume_slider.handle_event(ev)
                self._back_hovered = self._back_rect.collidepoint(ev.pos)
                if (
                    self._toggle_btn.is_hovered
                    or self._volume_slider.is_hovered
                    or self._volume_slider._dragging
                    or self._back_hovered
                ):
                    try:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    except Exception:
                        pass
                else:
                    try:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    except Exception:
                        pass

            # Mouse button click
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Toggle button
                if self._toggle_btn.handle_event(ev):
                    pass
                # Volume slider
                elif self._volume_slider.handle_event(ev):
                    pass
                # Back button
                elif self._back_rect.collidepoint(ev.pos):
                    play_sfx(SFX_CLICK_PATH)
                    self._next_state = GameState.MAIN_MENU

            # Mouse button release
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self._volume_slider.handle_event(ev)

            # Keyboard navigation
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    play_sfx(SFX_CLICK_PATH)
                    self._next_state = GameState.MAIN_MENU
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    self._focus_index = (self._focus_index - 1) % 3
                    self._update_keyboard_focus()
                elif ev.key in (pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
                    self._focus_index = (self._focus_index + 1) % 3
                    self._update_keyboard_focus()
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self._focus_index == 0:
                        self._toggle_btn.toggle()
                    elif self._focus_index == 1:
                        self._volume_slider.toggle_mute()
                    elif self._focus_index == 2:
                        play_sfx(SFX_CLICK_PATH)
                        self._next_state = GameState.MAIN_MENU
                elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                    if self._focus_index == 0:
                        self._toggle_btn.handle_event(ev)
                    elif self._focus_index == 1:
                        self._volume_slider.handle_event(ev)

    def _update_keyboard_focus(self) -> None:
        self._toggle_btn.is_focused = self._focus_index == 0
        self._volume_slider.is_focused = self._focus_index == 1
        self._back_focused = self._focus_index == 2

    def update(self, dt: float) -> None:
        del dt  # Unused for static frame

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self) -> None:
        """Render the complete settings screen layout, volume slider, and interactive toggle."""
        # 1. Base layout frame (cave + stone dialog + labels + volume slider track + back frame)
        if self._base_surf is not None:
            self._screen.blit(self._base_surf, (0, 0))
        else:
            self._screen.fill((35, 25, 30))

        # 2. Interactive Gesture Control ON/OFF button
        self._toggle_btn.draw(self._screen)

        # 3. Interactive Volume Slider (groove fill, knob, and overlays)
        self._volume_slider.draw(self._screen)

        # 4. Back button hover & keyboard focus feedback
        if self._back_hovered:
            self._screen.blit(self._back_hover_overlay, self._back_rect.topleft)

        if self._back_focused:
            self._screen.blit(
                self._back_focus_overlay,
                (self._back_rect.x - 3, self._back_rect.y - 3),
            )
