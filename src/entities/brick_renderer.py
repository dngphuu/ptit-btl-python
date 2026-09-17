"""
src/entities/brick_renderer.py
==============================
BrickRenderer is responsible ONLY for drawing bricks at their calculated positions.
Separates rendering concerns completely from grid layout and physics coordinates.
"""

from __future__ import annotations

import os

import pygame

from src.config import BRICK_COLORS, BRICKS_ASSET_DIR
from src.entities.brick import Brick
from src.entities.brick_grid import BrickGrid

# Fallback solid colors if asset images are unavailable
_FALLBACK_COLORS: dict[str, tuple[int, int, int]] = {
    "red": (210, 60, 64),
    "orange": (232, 137, 57),
    "yellow": (233, 204, 68),
    "green": (79, 175, 103),
    "blue": (57, 152, 216),
    "purple": (174, 81, 187),
}


class BrickRenderer:
    """Renderer dedicated solely to drawing bricks and brick grids.

    Maintains a surface cache scaled to the dynamic dimensions of the bricks,
    ensuring high rendering performance (60 FPS CPU-only) while supporting
    dynamic resolution and playfield sizing.
    """

    def __init__(self, asset_dir: str = BRICKS_ASSET_DIR) -> None:
        self.asset_dir: str = asset_dir
        # Raw trimmed sprites: (color_name, hp) -> pygame.Surface
        self._raw_sprites: dict[tuple[str, int], pygame.Surface] = {}
        # Scaled sprites cache: (color_name, hp, width_px, height_px) -> pygame.Surface
        self._scaled_cache: dict[tuple[str, int, int, int], pygame.Surface] = {}
        self._loaded: bool = False

    def _load_assets(self) -> None:
        """Load and trim original pixel-art sprite assets."""
        if self._loaded:
            return
        self._loaded = True

        if not os.path.exists(self.asset_dir):
            return

        state_names = {2: "normal", 1: "damaged"}
        for color in BRICK_COLORS:
            for hp, state_str in state_names.items():
                fname = f"{color}_{state_str}.png"
                fpath = os.path.join(self.asset_dir, fname)
                if os.path.exists(fpath):
                    raw = pygame.image.load(fpath).convert_alpha()
                    # Trim residual transparent padding so the brick fills its bounds
                    bbox = raw.get_bounding_rect()
                    trimmed = raw.subsurface(bbox).copy()
                    self._raw_sprites[(color, hp)] = trimmed

    def get_brick_surface(
        self, color: str, hp: int, target_width: int
    ) -> pygame.Surface | None:
        """Return a cached, pre-scaled surface for a brick of the given color and width.
        Height is scaled proportionally to maintain the 2.5D aspect ratio.
        """
        self._load_assets()

        hp_clamped = max(1, min(2, hp))
        color_lower = color.lower()
        key = (color_lower, hp_clamped, target_width)

        if key not in self._scaled_cache:
            raw = self._raw_sprites.get((color_lower, hp_clamped))
            if raw is not None:
                # Proportional height
                aspect = raw.get_height() / max(1, raw.get_width())
                target_height = max(1, round(target_width * aspect))
                scaled = pygame.transform.smoothscale(raw, (target_width, target_height))
                self._scaled_cache[key] = scaled
            else:
                return None

        return self._scaled_cache[key]

    def render(self, surface: pygame.Surface, grid: BrickGrid) -> None:
        """Render all alive bricks in the grid onto *surface*.

        Empty / destroyed cells are skipped, leaving the background cave wall visible.
        Draws from row 0 (top/furthest) to row N (bottom/closest) for correct z-sorting.
        """
        for r in range(grid.rows):
            for c in range(grid.cols):
                brick = grid[r][c]
                if brick is not None and brick.alive:
                    self.render_brick(surface, brick)

    def render_brick(self, surface: pygame.Surface, brick: Brick) -> None:
        """Render an individual brick at its pre-calculated screen coordinates."""
        if not brick.alive:
            return

        w = max(1, round(brick.width))
        # Logical height isn't used for sprite rendering because it squashes the 2.5D shape
        x = round(brick.x)
        y = round(brick.y)

        sprite = self.get_brick_surface(brick.color, brick.hp, w)
        if sprite is not None:
            # Anchor is (0.5, 1.0) -> center-bottom
            draw_x = x - sprite.get_width() // 2
            draw_y = y - sprite.get_height()
            surface.blit(sprite, (draw_x, draw_y))
        else:
            # Fallback: pixel-art styled rectangle with highlight and dark border
            base_col = _FALLBACK_COLORS.get(brick.color.lower(), (200, 200, 200))
            if brick.hp == 1:
                # Dim when damaged
                base_col = tuple(max(0, c - 45) for c in base_col)  # type: ignore[assignment]

            h = max(1, round(brick.height))
            draw_x = x - w // 2
            draw_y = y - h
            rect = pygame.Rect(draw_x, draw_y, w, h)
            pygame.draw.rect(surface, base_col, rect)
            # Dark outer pixel-art border
            pygame.draw.rect(surface, (25, 15, 20), rect, 1)
            # Inner top/left highlight
            if w > 4 and h > 4:
                pygame.draw.line(surface, (255, 255, 255, 80), (draw_x + 1, draw_y + 1), (draw_x + w - 2, draw_y + 1))
