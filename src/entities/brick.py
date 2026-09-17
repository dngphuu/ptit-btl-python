"""
src/entities/brick.py
=====================
Brick entity representing an individual brick inside the brick pool.
Maintains its grid coordinates (row, col), calculated screen bounds (x, y, width, height),
vitality state (alive, hp), and color.
"""

from __future__ import annotations

import pygame

from src.config import BRICK_COLORS


class Brick:
    """A single brick in the grid.

    Attributes:
        row (int): Grid row index (0-based, top to bottom).
        col (int): Grid column index (0-based, left to right).
        x (float): Calculated screen X coordinate.
        y (float): Calculated screen Y coordinate.
        width (float): Calculated brick width in pixels.
        height (float): Calculated brick height in pixels.
        color (str): Brick color identifier ("red", "orange", "yellow", etc.).
        hp (int): Hit points remaining (typically 2 = full, 1 = damaged, 0 = destroyed).
        alive (bool): Vitality status; False when destroyed, leaving row/col/x/y intact.
    """

    __slots__ = (
        "alive",
        "col",
        "color",
        "height",
        "hp",
        "row",
        "scale",
        "width",
        "x",
        "y",
    )

    def __init__(
        self,
        row: int,
        col: int,
        color: str | int,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        scale: float = 1.0,
        hp: int = 2,
        alive: bool = True,
    ) -> None:
        self.row: int = int(row)
        self.col: int = int(col)

        if isinstance(color, int):
            self.color: str = BRICK_COLORS[color % len(BRICK_COLORS)]
        else:
            self.color: str = color.lower()

        self.x: float = float(x)
        self.y: float = float(y)
        self.width: float = float(width)
        self.height: float = float(height)
        self.scale: float = float(scale)
        self.hp: int = int(hp)
        self.alive: bool = bool(alive)

    @property
    def rect(self) -> pygame.Rect:
        """Screen-space rectangle for collision detection (center-bottom pivot)."""
        w = self.width
        h = self.height
        return pygame.Rect(
            round(self.x - w / 2.0),
            round(self.y - h),
            round(w),
            round(h),
        )

    @property
    def colour_name(self) -> str:
        """Alias for color."""
        return self.color

    @property
    def colour(self) -> int:
        """Index of the color in BRICK_COLORS for compatibility."""
        return BRICK_COLORS.index(self.color) if self.color in BRICK_COLORS else 0

    @property
    def colour_idx(self) -> int:
        """Index of the color in BRICK_COLORS."""
        return self.colour

    def hit(self) -> bool:
        """Register a hit on this brick.

        Reduces HP by 1. If HP drops to 0, sets alive = False.
        Row, col, and calculated position remain completely unchanged.

        Returns:
            bool: True if the brick was destroyed by this hit, False otherwise.
        """
        if not self.alive:
            return False

        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def reset(self, hp: int = 2) -> None:
        """Revive the brick with the given HP, preserving position and grid cell."""
        self.hp = hp
        self.alive = True
