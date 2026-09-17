"""
src/entities/playfield.py
=========================
Playfield container rectangle representing the playable arena inside the stone frame.
All entities (brick pool, ball, paddle) live inside or relative to this boundary.
"""

from __future__ import annotations

import pygame

from src.config import (
    PLAYFIELD_HEIGHT,
    PLAYFIELD_WIDTH,
    PLAYFIELD_X,
    PLAYFIELD_Y,
)


class Playfield:
    """Container boundary for the gameplay area.

    Attributes:
        x (float): Top-left X coordinate on the screen / canvas.
        y (float): Top-left Y coordinate on the screen / canvas.
        width (float): Total width of the playfield.
        height (float): Total height of the playfield.
    """

    __slots__ = ("height", "width", "x", "y")

    def __init__(
        self,
        x: float = PLAYFIELD_X,
        y: float = PLAYFIELD_Y,
        width: float = PLAYFIELD_WIDTH,
        height: float = PLAYFIELD_HEIGHT,
    ) -> None:
        self.x: float = float(x)
        self.y: float = float(y)
        self.width: float = float(width)
        self.height: float = float(height)

    @property
    def rect(self) -> pygame.Rect:
        """Integer pygame.Rect representation of the playfield."""
        return pygame.Rect(
            round(self.x),
            round(self.y),
            round(self.width),
            round(self.height),
        )

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2.0

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2.0

    def get_left_edge(self, y: float) -> float:
        """Returns the actual left boundary at a given Y coordinate (slanted walls)."""
        # Linear approximation of the left stone pillar:
        # At y=240, x=205. At y=590, x=124. dx/dy = -0.231
        return 205 - 0.231 * (y - 240)

    def get_right_edge(self, y: float) -> float:
        """Returns the actual right boundary at a given Y coordinate (slanted walls)."""
        # Linear approximation of the right stone pillar:
        # At y=240, x=596. At y=590, x=674. dx/dy = 0.223
        return 596 + 0.223 * (y - 240)

    def set_bounds(self, x: float, y: float, width: float, height: float) -> None:
        """Update playfield coordinates (e.g. on window resize or canvas change)."""
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
