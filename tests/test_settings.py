"""
tests/test_settings.py
======================
Unit tests for SettingsMenu, VolumeSlider, and GameSettings audio & gesture controls.
"""

import os

import pygame
import pytest

from src.config import SCREEN_HEIGHT, SCREEN_WIDTH
from src.core.audio import play_music, play_sfx, set_music_volume
from src.core.settings import GameSettings
from src.core.states import GameState
from src.screens.settings import (
    _BACK_RECT,
    _SLIDER_MAX_X,
    _SLIDER_MIN_X,
    _SLIDER_RECT,
    _SPEAKER_RECT,
    _TOGGLE_RECT,
    SettingsMenu,
)


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


def test_game_settings_volume_controls(tmp_path, monkeypatch):
    test_json = str(tmp_path / "settings.json")
    monkeypatch.setattr("src.core.settings._SETTINGS_FILE", test_json)

    GameSettings.set_volume(0.8)
    assert GameSettings.get_volume() == 0.8
    assert GameSettings.music_volume == 0.8
    assert GameSettings.sfx_volume == 0.8

    # Test clamping
    GameSettings.set_volume(1.5)
    assert GameSettings.get_volume() == 1.0
    GameSettings.set_volume(-0.5)
    assert GameSettings.get_volume() == 0.0

    # Persistence reload
    GameSettings.set_volume(0.65)
    GameSettings.load()
    assert GameSettings.get_volume() == 0.65


def test_audio_module_volume():
    # Verify set_music_volume, play_music, and play_sfx execute without error
    GameSettings.set_volume(0.7)
    set_music_volume(0.7)
    play_music()
    play_sfx("non_existent_sfx.ogg")


def test_settings_menu_draw_and_layout():
    screen = pygame.display.get_surface()
    menu = SettingsMenu(screen)
    menu.reset_state()

    # Draw with various volume states
    GameSettings.set_volume(0.0)
    menu.draw()

    GameSettings.set_volume(0.5)
    menu.draw()

    GameSettings.set_volume(1.0)
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


def test_settings_menu_volume_slider_click():
    screen = pygame.display.get_surface()
    menu = SettingsMenu(screen)
    menu.reset_state()

    slider_y = _SLIDER_RECT.centery

    # Click at left end (0%)
    ev_left = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (_SLIDER_MIN_X, slider_y)}
    )
    menu.handle_events([ev_left])
    assert menu._volume_slider.value == 0.0
    assert GameSettings.get_volume() == 0.0

    # Click at right end (100%)
    ev_right = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (_SLIDER_MAX_X, slider_y)}
    )
    menu.handle_events([ev_right])
    assert menu._volume_slider.value == 1.0
    assert GameSettings.get_volume() == 1.0

    # Click at middle (50%)
    mid_x = (_SLIDER_MIN_X + _SLIDER_MAX_X) // 2
    ev_mid = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (mid_x, slider_y)})
    menu.handle_events([ev_mid])
    assert pytest.approx(menu._volume_slider.value, abs=0.05) == 0.5


def test_settings_menu_volume_slider_drag():
    screen = pygame.display.get_surface()
    menu = SettingsMenu(screen)
    menu.reset_state()

    slider_y = _SLIDER_RECT.centery
    mid_x = (_SLIDER_MIN_X + _SLIDER_MAX_X) // 2

    # Start drag at middle
    ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (mid_x, slider_y)})
    menu.handle_events([ev_down])
    assert menu._volume_slider._dragging is True

    # Drag to 80% position
    drag_x = _SLIDER_MIN_X + int(0.8 * (_SLIDER_MAX_X - _SLIDER_MIN_X))
    ev_motion = pygame.event.Event(
        pygame.MOUSEMOTION, {"pos": (drag_x, slider_y), "rel": (10, 0), "buttons": (1, 0, 0)}
    )
    menu.handle_events([ev_motion])
    assert pytest.approx(menu._volume_slider.value, abs=0.05) == 0.8

    # Release drag
    ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (drag_x, slider_y)})
    menu.handle_events([ev_up])
    assert menu._volume_slider._dragging is False
    assert pytest.approx(GameSettings.get_volume(), abs=0.05) == 0.8


def test_settings_menu_volume_speaker_mute_toggle():
    screen = pygame.display.get_surface()
    menu = SettingsMenu(screen)
    menu.reset_state()

    GameSettings.set_volume(0.7)
    speaker_pos = (_SPEAKER_RECT.centerx, _SPEAKER_RECT.centery)

    # Click speaker to mute
    ev_mute = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": speaker_pos})
    menu.handle_events([ev_mute])
    assert menu._volume_slider.value == 0.0

    # Click speaker again to restore
    ev_unmute = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": speaker_pos})
    menu.handle_events([ev_unmute])
    assert menu._volume_slider.value == 0.7


def test_settings_menu_keyboard_focus_and_slider():
    screen = pygame.display.get_surface()
    menu = SettingsMenu(screen)
    menu.reset_state()

    # Initially no focus (-1)
    assert menu._focus_index == -1

    # Press DOWN: focuses Toggle (0)
    menu.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})])
    assert menu._focus_index == 0
    assert menu._toggle_btn.is_focused is True
    assert menu._volume_slider.is_focused is False

    # Press DOWN again: focuses Volume Slider (1)
    menu.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})])
    assert menu._focus_index == 1
    assert menu._volume_slider.is_focused is True

    # Adjust volume with LEFT / RIGHT
    GameSettings.set_volume(0.5)
    menu.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})])
    assert pytest.approx(menu._volume_slider.value, abs=0.01) == 0.55

    menu.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})])
    assert pytest.approx(menu._volume_slider.value, abs=0.01) == 0.50

    # Space or M toggles mute
    menu.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})])
    assert menu._volume_slider.value == 0.0

    menu.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})])
    assert pytest.approx(menu._volume_slider.value, abs=0.01) == 0.50

    # Press DOWN again: focuses Back button (2)
    menu.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})])
    assert menu._focus_index == 2
    assert menu._back_focused is True

    # Press RETURN to activate Back button
    menu.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})])
    assert menu.next_state == GameState.MAIN_MENU


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
