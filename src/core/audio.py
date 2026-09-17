"""
src/core/audio.py
=================
Audio management for background music and sound effects.
"""

from __future__ import annotations

import logging
import os

import pygame

from src.config import MENU_BGM_PATH, MENU_BGM_VOLUME

logger = logging.getLogger(__name__)


def play_music(
    path: str = MENU_BGM_PATH,
    volume: float = MENU_BGM_VOLUME,
    loops: int = -1,
) -> None:
    """Load and play background music safely with Pygame mixer."""
    if not pygame.mixer.get_init():
        return

    if not os.path.exists(path):
        logger.warning("Audio file not found: %s", path)
        return

    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=loops)
    except pygame.error as exc:
        logger.warning("Failed to play music from %s: %s", path, exc)


def stop_music() -> None:
    """Stop currently playing background music."""
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()


def fadeout_music(ms: int = 500) -> None:
    """Fade out currently playing background music over *ms* milliseconds."""
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        pygame.mixer.music.fadeout(ms)
