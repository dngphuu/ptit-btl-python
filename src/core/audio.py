"""
src/core/audio.py
=================
Audio management for background music and sound effects.
Supports extracting background audio from video files if needed.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import Optional

import pygame

from src.config import MENU_BGM_PATH, MENU_BGM_VOLUME

logger = logging.getLogger(__name__)


def ensure_menu_bgm(
    video_path: str = "assets/backgrounds/Clouds.mp4",
    bgm_path: str = MENU_BGM_PATH,
) -> str:
    """Ensure the menu BGM file exists; extract from video if missing.

    Returns the path to the BGM audio file if available, else empty string.
    """
    if os.path.exists(bgm_path):
        return bgm_path

    if not os.path.exists(video_path):
        logger.warning("Cannot extract BGM: video file not found at %s", video_path)
        return ""

    os.makedirs(os.path.dirname(os.path.abspath(bgm_path)), exist_ok=True)

    # Check for ffmpeg via imageio_ffmpeg or system PATH
    ffmpeg_exe: Optional[str] = None
    try:
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg_exe = shutil.which("ffmpeg")

    if not ffmpeg_exe:
        logger.warning(
            "Neither imageio-ffmpeg nor system ffmpeg is available to extract audio from %s",
            video_path,
        )
        return ""

    logger.info("Extracting audio from %s -> %s", video_path, bgm_path)
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        video_path,
        "-vn",
        "-c:a",
        "libvorbis",
        "-q:a",
        "4",
        bgm_path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Audio extracted successfully.")
        return bgm_path
    except (subprocess.SubprocessError, OSError) as exc:
        logger.warning("Failed to extract audio using ffmpeg: %s", exc)
        return ""


def play_music(
    path: str = MENU_BGM_PATH,
    volume: float = MENU_BGM_VOLUME,
    loops: int = -1,
) -> None:
    """Load and play background music safely with Pygame mixer."""
    if not pygame.mixer.get_init():
        return

    if not os.path.exists(path):
        extracted = ensure_menu_bgm(bgm_path=path)
        if not extracted:
            return
        path = extracted

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
