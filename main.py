"""
main.py
=======
Entry point for VisionBrick – Hand-Tracked Brick Breaker.
Bootstraps pygame, runs the game-state machine.
"""

from __future__ import annotations

import sys

import pygame

from src.config import SCREEN_HEIGHT, SCREEN_WIDTH, TARGET_FPS
from src.core.states import GameState
from src.screens.gameplay import GameplayScreen
from src.screens.main_menu import MainMenu


def main() -> None:
    pygame.init()
    pygame.mixer.init()

    # Enable maximizing and resizing while automatically preserving the
    # logical 800x600 resolution and aspect ratio.
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.RESIZABLE | pygame.SCALED,
    )
    pygame.display.set_caption("Brick Breaker")
    clock = pygame.time.Clock()

    state: GameState = GameState.MAIN_MENU
    menu = MainMenu(screen)
    gameplay = GameplayScreen(screen)

    while state != GameState.QUIT:
        dt = clock.tick(TARGET_FPS) / 1000.0

        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                state = GameState.QUIT
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_F11 or (
                    ev.key == pygame.K_RETURN and (ev.mod & pygame.KMOD_ALT)
                ):
                    pygame.display.toggle_fullscreen()

        if state == GameState.MAIN_MENU:
            menu.handle_events(events)
            menu.update(dt)
            menu.draw()

            next_st = menu.next_state
            if next_st is not None:
                state = next_st
                menu._next_state = None  # reset so menu is ready upon return
                if state == GameState.PLAYING:
                    menu.stop_bgm()
                    gameplay.reset_state()
                    gameplay.play_bgm()
                elif state == GameState.SETTINGS:
                    print("[TODO] Transition to SETTINGS")
                    state = GameState.MAIN_MENU

        elif state == GameState.SETTINGS:
            # TODO: settings screen
            state = GameState.MAIN_MENU
            menu._next_state = None

        elif state == GameState.PLAYING:
            gameplay.handle_events(events)
            gameplay.update(dt)
            gameplay.draw()

            next_st = gameplay.next_state
            if next_st is not None:
                state = next_st
                gameplay.reset_state()
                gameplay.stop_bgm()
                if state == GameState.MAIN_MENU:
                    menu._next_state = None
                    menu.play_bgm()

        pygame.display.flip()

    menu.stop_bgm()
    gameplay.stop_bgm()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
