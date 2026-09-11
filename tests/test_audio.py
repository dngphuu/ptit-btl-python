"""
tests/test_audio.py
===================
Unit tests for background audio playback, safety, and extraction helpers.
"""

from __future__ import annotations

import os

import pygame
import pytest

from src.config import MENU_BGM_PATH
from src.core.audio import fadeout_music, play_music, stop_music
from src.screens.main_menu import MainMenu


@pytest.fixture(autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.mixer.init()
    yield
    stop_music()
    pygame.mixer.quit()
    pygame.quit()


def test_play_and_stop_music():
    if os.path.exists(MENU_BGM_PATH):
        play_music(MENU_BGM_PATH, volume=0.5, loops=-1)
        assert pygame.mixer.music.get_busy()
        fadeout_music(50)
        stop_music()
        assert not pygame.mixer.music.get_busy()


def test_play_music_missing_path():
    stop_music()
    play_music("non_existent_audio.ogg")
    # Should safely fail without crashing
    assert not pygame.mixer.music.get_busy()


def test_main_menu_bgm_integration():
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE | pygame.SCALED)
    menu = MainMenu(screen)
    assert pygame.mixer.music.get_busy()

    menu.stop_bgm()
    assert not pygame.mixer.music.get_busy()

    menu.play_bgm()
    assert pygame.mixer.music.get_busy()
    menu.stop_bgm()


def test_window_resizable_and_scaled_mode():
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE | pygame.SCALED)
    assert screen.get_size() == (800, 600)
