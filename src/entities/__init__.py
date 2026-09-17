"""
src/entities package
====================
Core game entities for VisionBrick.
Architecture:
    Playfield -> BrickGrid -> Brick[row][col] -> BrickRenderer
"""

from __future__ import annotations

from src.entities.brick import Brick
from src.entities.brick_grid import BrickGrid
from src.entities.brick_renderer import BrickRenderer
from src.entities.playfield import Playfield


def build_brick_grid(
    playfield: Playfield | None = None,
    pattern: list[list[str | int | None]] | None = None,
) -> list[Brick]:
    """Compatibility helper returning a flat list of bricks from a default BrickGrid."""
    if playfield is None:
        playfield = Playfield()
    grid = BrickGrid(playfield=playfield, pattern=pattern)
    return grid.all_bricks()


__all__ = [
    "Brick",
    "BrickGrid",
    "BrickRenderer",
    "Playfield",
    "build_brick_grid",
]
