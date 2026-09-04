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
from src.screens.main_menu import MainMenu


def main() -> None:
    pygame.init()
    # Mixer is initialised for future audio; the background GIF has no audio.
    pygame.mixer.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Brick Breaker")
    clock = pygame.time.Clock()

    state: GameState = GameState.MAIN_MENU
    menu = MainMenu(screen)

    while state != GameState.QUIT:
        dt = clock.tick(TARGET_FPS) / 1000.0

        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                state = GameState.QUIT

        if state == GameState.MAIN_MENU:
            menu.handle_events(events)
            menu.update(dt)
            menu.draw()

            next_st = menu.next_state
            if next_st is not None:
                state = next_st
                # TODO: remove these stubs once gameplay screens exist
                if state in (GameState.PLAYING, GameState.SETTINGS):
                    print(f"[TODO] Transition to {state.name}")
                    state = GameState.MAIN_MENU
                    menu._next_state = None  # reset so menu stays reactive

        elif state == GameState.SETTINGS:
            # TODO: settings screen
            state = GameState.MAIN_MENU
            menu._next_state = None

        elif state == GameState.PLAYING:
            # TODO: gameplay
            state = GameState.MAIN_MENU
            menu._next_state = None

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
