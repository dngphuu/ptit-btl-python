"""
src/ui/video_background.py
==========================
Streams and loops a video file (e.g., MP4) as a full-screen background
surface for Pygame screens using OpenCV.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import cv2
import pygame

logger = logging.getLogger(__name__)


class VideoBackground:
    """Streams and loops a video as a full-screen Pygame background."""

    def __init__(
        self,
        path: str,
        screen_size: tuple[int, int],
        loop: bool = True,
    ) -> None:
        """
        Parameters
        ----------
        path : str
            File-system path to the video file.
        screen_size : tuple[int, int]
            `(width, height)` of the display; frames are scaled to fit.
        loop : bool
            Whether to loop the video indefinitely.
        """
        self._path = os.path.abspath(path)
        self._screen_size = screen_size
        self._loop = loop

        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_delay: float = 1.0 / 30.0  # fallback 30 FPS
        self._elapsed: float = 0.0
        self._current_surf: Optional[pygame.Surface] = None

        self._init_capture()

    def _init_capture(self) -> None:
        if not os.path.exists(self._path):
            logger.warning("Video file not found: %s", self._path)
            self._fallback_surface()
            return

        self._cap = cv2.VideoCapture(self._path)
        if not self._cap.isOpened():
            logger.warning("Failed to open video file: %s", self._path)
            self._fallback_surface()
            return

        fps = self._cap.get(cv2.CAP_PROP_FPS)
        if fps and fps > 0:
            self._frame_delay = 1.0 / fps
        else:
            self._frame_delay = 1.0 / 30.0

        # Read and prepare the first frame immediately
        self._read_next_frame()

    def _fallback_surface(self) -> None:
        w, h = self._screen_size
        surf = pygame.Surface((w, h))
        surf.fill((20, 20, 35))
        self._current_surf = surf

    def _read_next_frame(self) -> bool:
        if self._cap is None or not self._cap.isOpened():
            return False

        ret, frame = self._cap.read()
        if not ret:
            if self._loop:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self._cap.read()
                if not ret:
                    return False
            else:
                return False

        # Resize to target screen size
        w, h = self._screen_size
        resized = cv2.resize(frame, (w, h))
        cv2.cvtColor(resized, cv2.COLOR_BGR2RGB, dst=resized)
        self._current_surf = pygame.image.frombuffer(resized.data, (w, h), "RGB").copy()
        return True

    def update(self, dt: float) -> None:
        """Advance video playback by *dt* seconds."""
        if self._cap is None or not self._cap.isOpened():
            return

        if dt <= 0:
            return

        self._elapsed += dt
        # Prevent spiral-of-death during large hitches or pauses
        max_accumulated = self._frame_delay * 5.0
        if self._elapsed > max_accumulated:
            self._elapsed = self._frame_delay

        while self._elapsed >= self._frame_delay:
            self._elapsed -= self._frame_delay
            ret = self._read_next_frame()
            if not ret:
                break

    def draw(self, surface: pygame.Surface) -> None:
        """Blit the current video frame onto the target surface."""
        if self._current_surf is not None:
            surface.blit(self._current_surf, (0, 0))

    def release(self) -> None:
        """Release underlying OpenCV VideoCapture resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def close(self) -> None:
        """Alias for release()."""
        self.release()

    def __del__(self) -> None:
        self.release()
