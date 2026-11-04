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
from src.core.settings import GameSettings

logger = logging.getLogger(__name__)


def set_music_volume(volume: float) -> None:
    """Update volume of currently playing background music."""
    if not pygame.mixer.get_init():
        return
    try:
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
    except pygame.error as exc:
        logger.warning("Failed to update music volume: %s", exc)


def play_music(
    path: str = MENU_BGM_PATH,
    volume: float | None = None,
    loops: int = -1,
) -> None:
    """Load and play background music safely with Pygame mixer."""
    if not pygame.mixer.get_init():
        return

    if not os.path.exists(path):
        logger.warning("Audio file not found: %s", path)
        return

    if volume is None:
        effective_volume = GameSettings.music_volume
    else:
        ratio = (volume / MENU_BGM_VOLUME) if MENU_BGM_VOLUME > 0 else 1.0
        effective_volume = max(0.0, min(1.0, ratio * GameSettings.music_volume))

    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(effective_volume)
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


_sfx_cache: dict[str, pygame.mixer.Sound] = {}


def play_sfx(path: str, volume: float = 1.0) -> None:
    """Load (and cache) and play a sound effect safely with Pygame mixer."""
    if not pygame.mixer.get_init():
        return

    if not os.path.exists(path):
        return

    try:
        if path not in _sfx_cache:
            _sfx_cache[path] = pygame.mixer.Sound(path)

        sound = _sfx_cache[path]
        eff_volume = max(0.0, min(1.0, volume * GameSettings.sfx_volume))
        sound.set_volume(eff_volume)
        sound.play()
    except pygame.error as exc:
        logger.warning("Failed to play sfx from %s: %s", path, exc)
