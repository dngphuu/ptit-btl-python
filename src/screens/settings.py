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
    SFX_CLICK_PATH,
)
from src.core.audio import play_sfx
from src.core.settings import GameSettings
from src.core.states import GameState

# ---------------------------------------------------------------------------
# Asset paths
# ---------------------------------------------------------------------------
_SETTINGS_UI_DIR = "assets/sprites/ui/settings"
_BASE_BG_PATH = os.path.join(_SETTINGS_UI_DIR, "settings_menu_base.png")
_BTN_TOGGLE_ON_PATH = os.path.join(_SETTINGS_UI_DIR, "btn_toggle_on.png")
_BTN_TOGGLE_OFF_PATH = os.path.join(_SETTINGS_UI_DIR, "btn_toggle_off.png")

# ---------------------------------------------------------------------------
# Layout coordinates (800 x 600 logical resolution)
# ---------------------------------------------------------------------------
_TOGGLE_RECT = pygame.Rect(417, 207, 178, 64)
_BACK_RECT = pygame.Rect(280, 366, 240, 94)

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
        self._hover_overlay.fill((255, 255, 255, 35))

        self._focus_overlay = pygame.Surface(
            (self.rect.width + 6, self.rect.height + 6), pygame.SRCALPHA
        )
        pygame.draw.rect(
            self._focus_overlay, (240, 200, 120, 160), self._focus_overlay.get_rect(), 2, border_radius=6
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


class SettingsMenu:
    """
    Settings menu screen matching mockups/settings_menu.png.

    Features:
      - Complete main layout matching the cave aesthetic.
      - Interactive ON/OFF toggle switch button for Gesture Control.
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
            self._base_surf = _load_image(
                MAIN_MENU_BG_PATH, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )

        # ── Toggle Button Sprites ─────────────────────────────────────────
        toggle_on_surf = _load_image(
            _BTN_TOGGLE_ON_PATH, (_TOGGLE_RECT.width, _TOGGLE_RECT.height)
        )
        toggle_off_surf = _load_image(
            _BTN_TOGGLE_OFF_PATH, (_TOGGLE_RECT.width, _TOGGLE_RECT.height)
        )

        self._toggle_btn = GestureToggleButton(
            _TOGGLE_RECT, toggle_on_surf, toggle_off_surf
        )

        # ── Back Button ───────────────────────────────────────────────────
        self._back_rect = _BACK_RECT
        self._back_hovered = False
        self._back_focused = False

        # Back button hover & focus overlays
        self._back_hover_overlay = pygame.Surface(self._back_rect.size, pygame.SRCALPHA)
        self._back_hover_overlay.fill((255, 255, 200, 30))
        pygame.draw.rect(
            self._back_hover_overlay,
            (255, 230, 160, 120),
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
        # 0: Gesture Toggle, 1: Back Button
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
                self._back_hovered = self._back_rect.collidepoint(ev.pos)
                if self._toggle_btn.is_hovered or self._back_hovered:
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
                # Back button
                elif self._back_rect.collidepoint(ev.pos):
                    play_sfx(SFX_CLICK_PATH)
                    self._next_state = GameState.MAIN_MENU

            # Keyboard navigation
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    play_sfx(SFX_CLICK_PATH)
                    self._next_state = GameState.MAIN_MENU
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    self._focus_index = (self._focus_index - 1) % 2
                    self._update_keyboard_focus()
                elif ev.key in (pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
                    self._focus_index = (self._focus_index + 1) % 2
                    self._update_keyboard_focus()
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self._focus_index == 0:
                        self._toggle_btn.toggle()
                    elif self._focus_index == 1:
                        play_sfx(SFX_CLICK_PATH)
                        self._next_state = GameState.MAIN_MENU
                elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                    if self._focus_index == 0:
                        self._toggle_btn.handle_event(ev)

    def _update_keyboard_focus(self) -> None:
        self._toggle_btn.is_focused = self._focus_index == 0
        self._back_focused = self._focus_index == 1

    def update(self, dt: float) -> None:
        del dt  # Unused for static frame

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self) -> None:
        """Render the complete settings screen layout and interactive toggle."""
        # 1. Base layout frame (cave + stone dialog + labels + volume slider + back frame)
        if self._base_surf is not None:
            self._screen.blit(self._base_surf, (0, 0))
        else:
            self._screen.fill((35, 25, 30))

        # 2. Interactive Gesture Control ON/OFF button
        self._toggle_btn.draw(self._screen)

        # 3. Back button hover & keyboard focus feedback
        if self._back_hovered:
            self._screen.blit(self._back_hover_overlay, self._back_rect.topleft)

        if self._back_focused:
            self._screen.blit(
                self._back_focus_overlay,
                (self._back_rect.x - 3, self._back_rect.y - 3),
            )
