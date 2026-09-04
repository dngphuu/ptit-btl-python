"""
src/core/states.py
==================
Game state machine enum.  The main loop transitions between these states.
"""

from enum import Enum, auto


class GameState(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    SETTINGS = auto()
    GAME_OVER = auto()
    QUIT = auto()
