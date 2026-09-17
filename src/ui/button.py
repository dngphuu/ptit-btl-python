"""
src/ui/button.py
================
Menu button component with hover and press visual feedback.
Supports rendering with a background surface or directly on pre-baked frames.
"""

from __future__ import annotations

import pygame
from src.core.audio import play_sfx
from src.config import SFX_CLICK_PATH

class MenuButton:
    """A rectangular button rendered with an optional stone background and centred text."""

    # Colour overlays for state feedback
    _HOVER_TINT: tuple[int, int, int, int] = (255, 255, 220, 32)
    _PRESS_TINT: tuple[int, int, int, int] = (0, 0, 0, 48)

    def __init__(
        self,
        rect: pygame.Rect,
        label: str = "",
        bg_surface: pygame.Surface | None = None,
        font: pygame.font.Font | None = None,
        text_color: tuple[int, int, int] = (66, 19, 14),
        hover_text_color: tuple[int, int, int] | None = (130, 38, 28),
        press_offset: int = 2,
    ) -> None:
        self.rect = rect
        self.label = label
        self.press_offset = press_offset
        self._font = font if font is not None else pygame.font.Font(None, 24)
        self._text_color = text_color
        self._hover_text_color = hover_text_color if hover_text_color is not None else text_color
        self._hovered = False
        self._pressed = False

        if bg_surface is not None:
            self._normal_surf: pygame.Surface | None = pygame.transform.smoothscale(
                bg_surface, rect.size
            )
            # Hover surface: slightly illuminated
            self._hover_surf: pygame.Surface | None = self._normal_surf.copy()
            h_overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            h_overlay.fill(self._HOVER_TINT)
            self._hover_surf.blit(h_overlay, (0, 0))

            # Pressed surface: slightly darkened
            self._press_surf: pygame.Surface | None = self._normal_surf.copy()
            p_overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            p_overlay.fill(self._PRESS_TINT)
            self._press_surf.blit(p_overlay, (0, 0))
        else:
            self._normal_surf = None
            self._hover_surf = None
            self._press_surf = None

        # Overlays for buttons rendered without dedicated background sprite
        self._overlay_hover = pygame.Surface(rect.size, pygame.SRCALPHA)
        self._overlay_hover.fill(self._HOVER_TINT)
        self._overlay_press = pygame.Surface(rect.size, pygame.SRCALPHA)
        self._overlay_press.fill(self._PRESS_TINT)

    # ------------------------------------------------------------------

    def update(self, events: list[pygame.event.Event]) -> bool:
        """Process events; returns True on a valid click (press + release inside)."""
        mp = pygame.mouse.get_pos()
        self._hovered = self.rect.collidepoint(mp)
        clicked = False
        for ev in events:
            if ev.type == pygame.MOUSEMOTION:
                pos = getattr(ev, "pos", mp)
                self._hovered = self.rect.collidepoint(pos)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pos = getattr(ev, "pos", mp)
                if self.rect.collidepoint(pos):
                    self._pressed = True
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                pos = getattr(ev, "pos", mp)
                if self._pressed and self.rect.collidepoint(pos):
                    clicked = True
                    play_sfx(SFX_CLICK_PATH)
                self._pressed = False
        return clicked

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button to *surface* with hover and press effects."""
        y_offset = self.press_offset if self._pressed else 0
        draw_rect = self.rect.move(0, y_offset)

        # 1. Background (if provided) or overlay
        if self._normal_surf is not None:
            if self._pressed and self._press_surf is not None:
                surface.blit(self._press_surf, draw_rect.topleft)
            elif self._hovered and self._hover_surf is not None:
                surface.blit(self._hover_surf, draw_rect.topleft)
            else:
                surface.blit(self._normal_surf, draw_rect.topleft)
        elif self._pressed:
            surface.blit(self._overlay_press, draw_rect.topleft)
        elif self._hovered:
            surface.blit(self._overlay_hover, draw_rect.topleft)

        # 2. Centred label
        if self.label:
            color = self._hover_text_color if self._hovered else self._text_color
            text = self._font.render(self.label, True, color)
            surface.blit(text, text.get_rect(center=draw_rect.center))
