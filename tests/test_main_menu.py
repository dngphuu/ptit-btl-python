"""
tests/test_main_menu.py
========================
Unit tests for MainMenu and MenuButton with the new cave design.
"""

from __future__ import annotations

import os

import pygame
import pytest

from src.core.states import GameState
from src.screens.main_menu import MainMenu
from src.ui.button import MenuButton


@pytest.fixture(autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.mixer.init()
    yield
    pygame.mixer.quit()
    pygame.quit()


def test_main_menu_init_and_draw():
    screen = pygame.display.set_mode((800, 600))
    menu = MainMenu(screen)

    assert menu.next_state is None
    assert len(menu._buttons) == 3

    # Test draw and update
    menu.draw()
    menu.update(0.016)
    menu.stop_bgm()


def test_main_menu_mouse_click_start():
    screen = pygame.display.set_mode((800, 600))
    menu = MainMenu(screen)

    # First button is START
    btn_start, state = menu._buttons[0]
    assert state == GameState.PLAYING

    # Simulate mouse click at center of START button
    cx, cy = btn_start.rect.center
    down_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (cx, cy)})
    up_ev = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (cx, cy)})

    menu.handle_events([down_ev, up_ev])
    assert menu.next_state == GameState.PLAYING
    menu.stop_bgm()


def test_main_menu_mouse_click_exit():
    screen = pygame.display.set_mode((800, 600))
    menu = MainMenu(screen)

    btn_exit, state = menu._buttons[2]
    assert state == GameState.QUIT

    cx, cy = btn_exit.rect.center
    down_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (cx, cy)})
    up_ev = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (cx, cy)})

    menu.handle_events([down_ev, up_ev])
    assert menu.next_state == GameState.QUIT
    menu.stop_bgm()


def test_main_menu_keyboard_navigation():
    screen = pygame.display.set_mode((800, 600))
    menu = MainMenu(screen)

    # Press DOWN -> index moves from 0 (START) to 1 (SETTINGS)
    down_key = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
    menu.handle_events([down_key])
    assert menu._selected_index == 1

    # Press ENTER -> activates SETTINGS
    enter_key = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
    menu.handle_events([enter_key])
    assert menu.next_state == GameState.SETTINGS
    menu.stop_bgm()


def test_main_menu_escape_key():
    screen = pygame.display.set_mode((800, 600))
    menu = MainMenu(screen)

    esc_key = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    menu.handle_events([esc_key])
    assert menu.next_state == GameState.QUIT
    menu.stop_bgm()


def test_menu_button_states():
    rect = pygame.Rect(100, 100, 200, 50)
    btn = MenuButton(rect, "TEST")

    surf = pygame.Surface((400, 300))
    btn.draw(surf)

    # Hover
    motion = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (150, 125)})
    btn.update([motion])
    assert btn._hovered

    # Draw while hovered
    btn.draw(surf)
