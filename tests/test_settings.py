"""
tests/test_settings.py
======================
Unit tests for SettingsMenu and GameSettings gesture control.
"""

import os
import pygame
import pytest

from src.config import SCREEN_HEIGHT, SCREEN_WIDTH
from src.core.settings import GameSettings
from src.core.states import GameState
from src.screens.settings import SettingsMenu, _TOGGLE_RECT, _BACK_RECT


@pytest.fixture(autouse=True)
def init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    yield
    pygame.quit()


def test_game_settings_gesture_toggle(tmp_path, monkeypatch):
    test_json = str(tmp_path / "settings.json")
    monkeypatch.setattr("src.core.settings._SETTINGS_FILE", test_json)

    GameSettings.control_mode = "gesture"
    assert GameSettings.is_gesture_on() is True

    GameSettings.set_gesture_control(False)
    assert GameSettings.is_gesture_on() is False
    assert GameSettings.control_mode == "keyboard"

    GameSettings.set_gesture_control(True)
    assert GameSettings.is_gesture_on() is True
    assert GameSettings.control_mode == "gesture"


def test_settings_menu_draw_and_layout():
    screen = pygame.display.get_surface()
    menu = SettingsMenu(screen)
    menu.reset_state()
    # Draw with no exceptions
    menu.draw()


def test_settings_menu_toggle_click():
    screen = pygame.display.get_surface()
    menu = SettingsMenu(screen)
    menu.reset_state()

    # Initial state
    GameSettings.set_gesture_control(True)
    assert menu._toggle_btn.is_on() is True

    # Click on the OFF half of toggle button (right half)
    click_x = _TOGGLE_RECT.x + int(_TOGGLE_RECT.width * 0.75)
    click_y = _TOGGLE_RECT.y + _TOGGLE_RECT.height // 2
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (click_x, click_y)})
    menu.handle_events([ev])

    assert menu._toggle_btn.is_on() is False
    assert GameSettings.is_gesture_on() is False

    # Click on the ON half of toggle button (left half)
    click_x = _TOGGLE_RECT.x + int(_TOGGLE_RECT.width * 0.25)
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (click_x, click_y)})
    menu.handle_events([ev])

    assert menu._toggle_btn.is_on() is True
    assert GameSettings.is_gesture_on() is True


def test_settings_menu_back_button():
    screen = pygame.display.get_surface()
    menu = SettingsMenu(screen)
    menu.reset_state()
    assert menu.next_state is None

    # Click on Back button
    click_x = _BACK_RECT.centerx
    click_y = _BACK_RECT.centery
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (click_x, click_y)})
    menu.handle_events([ev])

    assert menu.next_state == GameState.MAIN_MENU


def test_settings_menu_esc_key():
    screen = pygame.display.get_surface()
    menu = SettingsMenu(screen)
    menu.reset_state()
    assert menu.next_state is None

    ev = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    menu.handle_events([ev])

    assert menu.next_state == GameState.MAIN_MENU
