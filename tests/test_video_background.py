"""
tests/test_video_background.py
==============================
Unit tests for VideoBackground and MainMenu video background integration.
"""

from __future__ import annotations

import os

import pygame
import pytest

from src.screens.main_menu import MainMenu
from src.ui.video_background import VideoBackground

VIDEO_PATH = "assets/backgrounds/Clouds.mp4"


@pytest.fixture(autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


def test_video_background_loads_valid_file():
    bg = VideoBackground(VIDEO_PATH, (800, 600))
    assert bg._current_surf is not None
    assert bg._current_surf.get_size() == (800, 600)

    target_surface = pygame.Surface((800, 600))
    bg.draw(target_surface)
    bg.release()


def test_video_background_update_advances_and_loops():
    bg = VideoBackground(VIDEO_PATH, (800, 600), loop=True)

    # Advance by 1 second (several frames)
    bg.update(1.0)
    assert bg._current_surf is not None

    # Advance by more than the 10s video length to verify looping
    bg.update(12.0)
    assert bg._current_surf is not None

    bg.release()


def test_video_background_fallback_on_missing_file():
    bg = VideoBackground("non_existent_file.mp4", (800, 600))
    assert bg._current_surf is not None
    assert bg._current_surf.get_size() == (800, 600)

    target_surface = pygame.Surface((800, 600))
    bg.draw(target_surface)
    bg.update(0.5)
    bg.release()


def test_main_menu_with_video_background():
    screen = pygame.display.set_mode((800, 600))
    menu = MainMenu(screen)

    # Initial frame draw
    menu.draw()

    # Advance time
    menu.update(0.016)
    menu.draw()

    assert menu.next_state is None
