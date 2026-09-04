"""
src/ui/button.py
================
Pixel-art menu button: a Kenney 9-slice panel with a centred label.
Supports hover (brightness up) and press (darken) visual feedback.
"""

from __future__ import annotations

import pygame

from src.ui.nine_slice import NineSlicePanel


class MenuButton:
    """A rectangular button rendered with an image background (or panel) and centred text."""

    # Colour overlays for state feedback
    _HOVER_TINT: tuple[int, int, int, int] = (255, 255, 210, 35)
    _PRESS_TINT: tuple[int, int, int, int] = (0, 0, 0, 55)

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        bg_surface: pygame.Surface | NineSlicePanel | None = None,
        font: pygame.font.Font | None = None,
        text_color: tuple[int, int, int] = (75, 42, 7),
        *,
        panel: NineSlicePanel | None = None,
    ) -> None:
        self.rect = rect
        self.label = label
        self._font = font if font is not None else pygame.font.Font(None, 24)
        self._text_color = text_color
        self._hovered = False
        self._pressed = False

        target_bg = panel if panel is not None else bg_surface
        if isinstance(target_bg, pygame.Surface):
            self._panel: NineSlicePanel | None = None
            # Pre-render normal surface scaled to button rect
            self._normal_surf: pygame.Surface | None = pygame.transform.smoothscale(
                target_bg, rect.size
            )

            # Hover surface (tinted with alpha preserved)
            self._hover_surf: pygame.Surface | None = self._normal_surf.copy()
            h_overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            h_overlay.fill(self._HOVER_TINT)
            h_overlay.blit(self._normal_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self._hover_surf.blit(h_overlay, (0, 0))

            # Pressed surface
            self._press_surf: pygame.Surface | None = self._normal_surf.copy()
            p_overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            p_overlay.fill(self._PRESS_TINT)
            p_overlay.blit(self._normal_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self._press_surf.blit(p_overlay, (0, 0))
        elif isinstance(target_bg, NineSlicePanel):
            self._panel = target_bg
            self._normal_surf = None
            self._hover_surf = None
            self._press_surf = None
        else:
            self._panel = None
            self._normal_surf = None
            self._hover_surf = None
            self._press_surf = None

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
                self._pressed = False
        return clicked

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button to *surface*."""
        # 1. Background
        if (
            self._normal_surf is not None
            and self._press_surf is not None
            and self._hover_surf is not None
        ):
            if self._pressed:
                surface.blit(self._press_surf, self.rect.topleft)
            elif self._hovered:
                surface.blit(self._hover_surf, self.rect.topleft)
            else:
                surface.blit(self._normal_surf, self.rect.topleft)
        elif self._panel is not None:
            self._panel.draw(surface, self.rect)
            if self._pressed or self._hovered:
                overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
                overlay.fill(self._PRESS_TINT if self._pressed else self._HOVER_TINT)
                surface.blit(overlay, self.rect.topleft)

        # 2. Centred label
        text = self._font.render(self.label, True, self._text_color)
        surface.blit(text, text.get_rect(center=self.rect.center))
