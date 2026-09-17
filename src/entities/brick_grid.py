"""
src/entities/brick_grid.py
==========================
BrickGrid manages the 2D grid[row][col] coordinate model and responsive layout calculation
for all bricks inside the playfield.

Calculates brick dimensions and screen positions dynamically based on the container pool
and keeps the brick grid centered horizontally without hardcoded positions.
"""

from __future__ import annotations

from typing import Iterator

from src.config import (
    BRICK_GRID_COLS,
    BRICK_GRID_ROWS,
    BRICK_HEIGHT,
    BRICK_HORIZONTAL_GAP,
    BRICK_MARGIN_TOP,
    BRICK_MARGIN_X,
    BRICK_MAX_HEIGHT_RATIO,
    BRICK_VERTICAL_GAP,
)
from src.entities.brick import Brick
from src.entities.playfield import Playfield


class BrickGrid:
    """Manages the 2D brick wall layout inside the Playfield.

    Coordinate model:
        grid[row][col] -> Brick or None

    Calculates actual screen coordinates (x, y, width, height) dynamically
    from the playfield dimensions, ensuring the grid is centered, properly
    spaced, and constrained within the upper portion of the pool.
    """

    def __init__(
        self,
        playfield: Playfield,
        rows: int = BRICK_GRID_ROWS,
        cols: int = BRICK_GRID_COLS,
        pattern: list[list[str | int | None]] | None = None,
        horizontal_gap: float = BRICK_HORIZONTAL_GAP,
        vertical_gap: float = BRICK_VERTICAL_GAP,
        margin_x: float = BRICK_MARGIN_X,
        margin_top: float = BRICK_MARGIN_TOP,
        brick_height: float = BRICK_HEIGHT,
        max_height_ratio: float = BRICK_MAX_HEIGHT_RATIO,
    ) -> None:
        self.playfield: Playfield = playfield
        self.rows: int = int(rows)
        self.cols: int = int(cols)
        self.horizontal_gap: float = float(horizontal_gap)
        self.vertical_gap: float = float(vertical_gap)
        self.margin_x: float = float(margin_x)
        self.margin_top: float = float(margin_top)
        self.brick_height: float = float(brick_height)
        self.max_height_ratio: float = float(max_height_ratio)

        # 2D grid coordinate model: grid[row][col]
        self.grid: list[list[Brick | None]] = []

        self._build_grid(pattern)
        self.recalculate_layout()

    # ------------------------------------------------------------------
    # Grid Construction & Layout
    # ------------------------------------------------------------------

    def _build_grid(self, pattern: list[list[str | int | None]] | None = None) -> None:
        """Instantiate Brick entities in the 2D grid structure."""
        if pattern is None:
            pattern = self._default_pattern()

        self.grid = []
        for r in range(self.rows):
            row_list: list[Brick | None] = []
            pattern_row = pattern[r] if r < len(pattern) else []
            for c in range(self.cols):
                color_val = pattern_row[c] if c < len(pattern_row) else None
                if color_val is not None:
                    row_list.append(Brick(row=r, col=c, color=color_val))
                else:
                    row_list.append(None)
            self.grid.append(row_list)

    def _default_pattern(self) -> list[list[str | int | None]]:
        """Mockup-matching color sequence: top red, orange, yellow, blue, green, red."""
        color_palette = [
            "red",  # Row 0
            "orange",  # Row 1
            "yellow",  # Row 2
            "blue",  # Row 3
            "green",  # Row 4
            "red",  # Row 5
        ]
        pattern: list[list[str | int | None]] = []
        for r in range(self.rows):
            color = color_palette[r % len(color_palette)]
            pattern.append([color] * self.cols)
        return pattern

    def recalculate_layout(self, playfield: Playfield | None = None) -> None:
        """Recalculate screen coordinates and dimensions for all bricks.

        Applies a trapezoidal perspective projection:
        - Top row is narrower and scaled down (depth/distance).
        - Bottom row is wider and scaled up (closer to camera).
        - t = row / (rows - 1)
        """
        if playfield is not None:
            self.playfield = playfield

        # 1. Determine available pool width at the bottom (closest)
        bottom_pool_width = max(10.0, self.playfield.width - 2.0 * self.margin_x)
        # Top row is narrower due to perspective (e.g., 85% width)
        top_pool_width = bottom_pool_width * 0.85

        min_scale = 0.85
        max_scale = 1.15

        # 2. Precalculate row scales
        row_scales = []
        for r in range(self.rows):
            t = r / max(1, self.rows - 1)
            row_scales.append(min_scale + (max_scale - min_scale) * t)

        # 3. Calculate bounded brick height
        max_pool_height = self.playfield.height * self.max_height_ratio - self.margin_top
        available_brick_height_sum = max_pool_height - (self.rows - 1) * self.vertical_gap
        
        sum_scales = sum(row_scales)
        if sum_scales > 0:
            max_h_per_scaled_brick = available_brick_height_sum / sum_scales
        else:
            max_h_per_scaled_brick = self.brick_height
            
        actual_brick_height = min(self.brick_height, max(1.0, max_h_per_scaled_brick))

        # 4. Position rows cumulatively
        pool_y_top = self.playfield.y + self.margin_top
        current_y = pool_y_top

        for r in range(self.rows):
            t = r / max(1, self.rows - 1)
            row_scale = row_scales[r]
            
            row_width = top_pool_width + (bottom_pool_width - top_pool_width) * t
            
            # Calculate brick width for this specific row
            brick_width = (row_width - (self.cols - 1) * self.horizontal_gap) / self.cols
            brick_width = max(1.0, brick_width)

            # Center the row horizontally
            total_grid_width = self.cols * brick_width + (self.cols - 1) * self.horizontal_gap
            pool_x = self.playfield.x + (self.playfield.width - total_grid_width) / 2.0

            row_y = current_y

            for c in range(self.cols):
                brick = self.grid[r][c]
                if brick is not None:
                    cx = pool_x + c * (brick_width + self.horizontal_gap) + brick_width / 2.0
                    cy = row_y + actual_brick_height * row_scale

                    brick.x = cx
                    brick.y = cy
                    brick.width = brick_width
                    brick.height = actual_brick_height * row_scale
                    brick.scale = row_scale
                    
            # Advance Y for next row (constant visual vertical gap)
            current_y += actual_brick_height * row_scale + self.vertical_gap

    # ------------------------------------------------------------------
    # Query & Access
    # ------------------------------------------------------------------

    def __getitem__(self, row: int) -> list[Brick | None]:
        """Enable direct grid[row][col] access."""
        return self.grid[row]

    def get_brick(self, row: int, col: int) -> Brick | None:
        """Safely fetch brick at grid[row][col], or None if out of bounds/empty."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None

    def alive_bricks(self) -> list[Brick]:
        """Return a flat list of all active (undestroyed) bricks."""
        return [brick for row in self.grid for brick in row if brick is not None and brick.alive]

    def all_bricks(self) -> list[Brick]:
        """Return a flat list of all bricks (both alive and destroyed)."""
        return [brick for row in self.grid for brick in row if brick is not None]

    def count_alive(self) -> int:
        """Count currently remaining alive bricks."""
        return sum(1 for row in self.grid for brick in row if brick is not None and brick.alive)

    def all_destroyed(self) -> bool:
        """Check if all bricks in the grid are destroyed."""
        return self.count_alive() == 0

    def reset(self) -> None:
        """Revive all bricks while keeping their positions and grid assignments."""
        for row in self.grid:
            for brick in row:
                if brick is not None:
                    brick.reset()

    def __iter__(self) -> Iterator[Brick]:
        """Iterate over all active (alive) bricks."""
        return iter(self.alive_bricks())

    def __len__(self) -> int:
        """Return the number of alive bricks."""
        return self.count_alive()
