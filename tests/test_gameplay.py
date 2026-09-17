"""
tests/test_gameplay.py
======================
Unit tests for GameplayScreen and exit button interaction.
"""

from __future__ import annotations

import os

import pygame
import pytest

from src.core.states import GameState
from src.screens.gameplay import GameplayScreen


@pytest.fixture(autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.mixer.init()
    yield
    pygame.mixer.quit()
    pygame.quit()


def test_gameplay_init_and_draw():
    screen = pygame.display.set_mode((800, 600))
    gameplay = GameplayScreen(screen)

    assert gameplay.next_state is None
    assert not gameplay.is_paused
    assert gameplay.score == 0
    assert gameplay.level == 1
    assert gameplay.lives == 3

    # Test update and draw without errors
    gameplay.update(0.016)
    gameplay.draw()


def test_gameplay_exit_button_click():
    screen = pygame.display.set_mode((800, 600))
    gameplay = GameplayScreen(screen)

    # Click center of exit button
    cx, cy = gameplay.exit_button.rect.center
    down_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (cx, cy)})
    up_ev = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (cx, cy)})

    gameplay.handle_events([down_ev, up_ev])
    assert gameplay.next_state == GameState.MAIN_MENU


def test_gameplay_escape_key_exits():
    screen = pygame.display.set_mode((800, 600))
    gameplay = GameplayScreen(screen)

    esc_key = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    gameplay.handle_events([esc_key])
    assert gameplay.next_state == GameState.MAIN_MENU


def test_gameplay_pause_button_and_key():
    screen = pygame.display.set_mode((800, 600))
    gameplay = GameplayScreen(screen)

    assert not gameplay.is_paused

    # Toggle with pause button click
    cx, cy = gameplay.pause_button.rect.center
    down_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (cx, cy)})
    up_ev = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (cx, cy)})
    gameplay.handle_events([down_ev, up_ev])
    assert gameplay.is_paused

    # Toggle with 'p' key
    p_key = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_p})
    gameplay.handle_events([p_key])
    assert not gameplay.is_paused


def test_gameplay_reset_state():
    screen = pygame.display.set_mode((800, 600))
    gameplay = GameplayScreen(screen)

    esc_key = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    gameplay.handle_events([esc_key])
    assert gameplay.next_state == GameState.MAIN_MENU

    gameplay.reset_state()
    assert gameplay.next_state is None


def test_menu_to_gameplay_to_menu_loop():
    screen = pygame.display.set_mode((800, 600))
    from src.screens.main_menu import MainMenu

    menu = MainMenu(screen)
    gameplay = GameplayScreen(screen)

    # 1. In main menu, click START
    start_btn, _ = menu._buttons[0]
    cx, cy = start_btn.rect.center
    down_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (cx, cy)})
    up_ev = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (cx, cy)})
    menu.handle_events([down_ev, up_ev])

    assert menu.next_state == GameState.PLAYING

    # Transition to PLAYING
    state = menu.next_state
    menu._next_state = None
    gameplay.reset_state()
    assert state == GameState.PLAYING

    # 2. In gameplay, click EXIT
    ecx, ecy = gameplay.exit_button.rect.center
    exit_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (ecx, ecy)})
    exit_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (ecx, ecy)})
    gameplay.handle_events([exit_down, exit_up])

    assert gameplay.next_state == GameState.MAIN_MENU

    # Transition back to MAIN_MENU
    state = gameplay.next_state
    gameplay.reset_state()
    menu._next_state = None
    assert state == GameState.MAIN_MENU
    menu.stop_bgm()


def test_gameplay_heart_rendering():
    screen = pygame.display.set_mode((800, 600))
    gameplay = GameplayScreen(screen)

    # Verify heart sprites are loaded
    assert gameplay._heart_surf is not None
    assert gameplay._heart_dim_surf is not None

    # Test full lives (3/3)
    gameplay.lives = 3
    gameplay.draw()

    # Test reduced lives (1/3)
    gameplay.lives = 1
    gameplay.draw()

    # Test 0 lives
    gameplay.lives = 0
    gameplay.draw()

    # Test extra lives (> 5)
    gameplay.lives = 7
    gameplay.draw()


def test_bgm_separation():
    screen = pygame.display.set_mode((800, 600))
    from src.screens.main_menu import MainMenu

    menu = MainMenu(screen)
    gameplay = GameplayScreen(screen)

    # Main menu BGM is playing initially
    assert pygame.mixer.music.get_busy()

    # Transition to gameplay: stop menu BGM
    menu.stop_bgm()
    assert not pygame.mixer.music.get_busy()

    # Gameplay BGM play/stop handles missing file or custom file gracefully
    gameplay.play_bgm()
    gameplay.stop_bgm()
    assert not pygame.mixer.music.get_busy()

    # Return to menu resumes menu BGM
    menu.play_bgm()
    assert pygame.mixer.music.get_busy()
    menu.stop_bgm()
