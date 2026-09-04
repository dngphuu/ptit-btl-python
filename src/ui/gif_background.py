"""
src/ui/gif_background.py
========================
Loads an animated GIF as a sequence of pygame Surfaces and loops through
them at the frame rate encoded in the GIF.

No audio is loaded (pygame-ce never reads GIF audio).
"""

from __future__ import annotations

import pygame


class GifBackground:
    """Plays an animated GIF as a full-screen background."""

    def __init__(self, path: str, screen_size: tuple[int, int]) -> None:
        """
        Parameters
        ----------
        path : str
            File-system path to the `.gif`.
        screen_size : tuple[int, int]
            `(width, height)` of the display; frames are scaled to cover it.
        """
        self._frames: list[pygame.Surface] = []
        self._delays: list[float] = []  # per-frame durations in seconds
        self._elapsed: float = 0.0
        self._current: int = 0

        self._load(path, screen_size)

    # ------------------------------------------------------------------

    def _load(self, path: str, size: tuple[int, int]) -> None:
        w, h = size
        animation = pygame.image.load_animation(path)
        # pygame-ce returns list[(Surface, delay_ms), ...]
        for frame_surf, delay_ms in animation:
            scaled = pygame.transform.smoothscale(frame_surf.convert(), (w, h))
            self._frames.append(scaled)
            self._delays.append(max(delay_ms, 1) / 1000.0)  # ms -> s, clamp >=1ms

    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance the animation by *dt* seconds."""
        if len(self._frames) <= 1:
            return
        self._elapsed += dt
        while self._elapsed >= self._delays[self._current]:
            self._elapsed -= self._delays[self._current]
            self._current = (self._current + 1) % len(self._frames)

    def draw(self, surface: pygame.Surface) -> None:
        """Blit the current frame at (0, 0)."""
        surface.blit(self._frames[self._current], (0, 0))
