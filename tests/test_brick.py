"""
tests/test_brick.py
===================
Unit tests for the Brick Pool architecture:
  Playfield -> BrickGrid -> Brick[row][col] -> BrickRenderer
"""

from __future__ import annotations

import os

import pygame
import pytest

from src.config import (
    BRICK_COLORS,
    BRICK_GRID_COLS,
    BRICK_GRID_ROWS,
    PLAYFIELD_HEIGHT,
    PLAYFIELD_WIDTH,
    PLAYFIELD_X,
    PLAYFIELD_Y,
)
from src.entities import (
    Brick,
    BrickGrid,
    BrickRenderer,
    Playfield,
    build_brick_grid,
)


@pytest.fixture(autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


# ---------------------------------------------------------------------------
# 1. Playfield tests
# ---------------------------------------------------------------------------


def test_playfield_initialization_and_bounds():
    pf = Playfield(x=100, y=200, width=500, height=400)
    assert pf.x == 100
    assert pf.y == 200
    assert pf.width == 500
    assert pf.height == 400
    assert pf.left == 100
    assert pf.right == 600
    assert pf.top == 200
    assert pf.bottom == 600
    assert pf.center_x == 350
    assert pf.center_y == 400

    rect = pf.rect
    assert rect == pygame.Rect(100, 200, 500, 400)

    # Test dynamic bounds update
    pf.set_bounds(50, 80, 600, 450)
    assert pf.x == 50
    assert pf.width == 600


# ---------------------------------------------------------------------------
# 2. Brick tests
# ---------------------------------------------------------------------------


def test_brick_initialization_and_properties():
    brick = Brick(row=2, col=5, color="yellow", x=250.0, y=300.0, width=40.0, height=16.0, hp=2)

    assert brick.row == 2
    assert brick.col == 5
    assert brick.color == "yellow"
    assert brick.x == 250.0
    assert brick.y == 300.0
    assert brick.width == 40.0
    assert brick.height == 16.0
    assert brick.hp == 2
    assert brick.alive is True
    assert brick.rect == pygame.Rect(250 - 20, 300 - 16, 40, 16)


def test_brick_destruction_preserves_position():
    brick = Brick(row=1, col=3, color="red", x=180.0, y=240.0, width=42.0, height=16.0, hp=2)

    # First hit damages brick
    destroyed = brick.hit()
    assert destroyed is False
    assert brick.hp == 1
    assert brick.alive is True
    assert (brick.row, brick.col) == (1, 3)
    assert (brick.x, brick.y) == (180.0, 240.0)

    # Second hit destroys brick
    destroyed = brick.hit()
    assert destroyed is True
    assert brick.hp == 0
    assert brick.alive is False

    # CRITICAL: row/col and calculated position remain completely unchanged!
    assert (brick.row, brick.col) == (1, 3)
    assert (brick.x, brick.y) == (180.0, 240.0)
    assert (brick.width, brick.height) == (42.0, 16.0)

    # Subsequent hit on dead brick
    assert brick.hit() is False


# ---------------------------------------------------------------------------
# 3. BrickGrid & Layout calculation tests
# ---------------------------------------------------------------------------


def test_brick_grid_coordinate_model():
    pf = Playfield(x=PLAYFIELD_X, y=PLAYFIELD_Y, width=PLAYFIELD_WIDTH, height=PLAYFIELD_HEIGHT)
    grid = BrickGrid(pf, rows=BRICK_GRID_ROWS, cols=BRICK_GRID_COLS)

    # 2D indexing: grid[row][col]
    assert len(grid.grid) == BRICK_GRID_ROWS
    for r in range(BRICK_GRID_ROWS):
        assert len(grid.grid[r]) == BRICK_GRID_COLS
        for c in range(BRICK_GRID_COLS):
            brick = grid[r][c]
            assert brick is not None
            assert brick.row == r
            assert brick.col == c
            assert grid.get_brick(r, c) is brick

    assert grid.count_alive() == BRICK_GRID_ROWS * BRICK_GRID_COLS


def test_brick_grid_formula_and_centering():
    pf = Playfield(x=176, y=236, width=448, height=340)
    margin_x = 14
    margin_top = 2
    h_gap = 2
    v_gap = 2
    cols = 10
    rows = 9

    grid = BrickGrid(
        pf,
        rows=rows,
        cols=cols,
        horizontal_gap=h_gap,
        vertical_gap=v_gap,
        margin_x=margin_x,
        margin_top=margin_top,
        brick_height=16,
    )

    # Expected formula (trapezoidal perspective):
    # bottom_pool_width = pf.width - 2 * margin_x = 448 - 28 = 420
    # top_pool_width = 420 * 0.85 = 357.0
    # For row r, t = r / 8
    # row_width = 357.0 + (420 - 357.0) * t
    # brick_width = (row_width - 9 * h_gap) / cols
    # Calculate expected scale factor for actual_brick_height
    row_scales = [0.85 + (1.15 - 0.85) * (r / 8.0) for r in range(rows)]
    max_pool_height = pf.height * 0.55 - margin_top
    available_h = max_pool_height - (rows - 1) * v_gap
    expected_actual_height = min(16.0, available_h / sum(row_scales))

    expected_current_y = pf.y + margin_top

    for r in range(rows):
        t = r / 8.0
        expected_row_width = 357.0 + (420.0 - 357.0) * t
        expected_brick_width = (expected_row_width - 9 * h_gap) / cols
        expected_total_grid_width = cols * expected_brick_width + 9 * h_gap
        expected_pool_x = 176 + (448 - expected_total_grid_width) / 2.0
        
        expected_scale = row_scales[r]
        expected_y = expected_current_y + expected_actual_height * expected_scale

        for c in range(cols):
            b = grid[r][c]
            assert b is not None
            expected_cx = expected_pool_x + c * (expected_brick_width + h_gap) + expected_brick_width / 2.0
            assert pytest.approx(b.x, abs=0.01) == expected_cx
            assert pytest.approx(b.y, abs=0.01) == expected_y
            
        expected_current_y += expected_actual_height * expected_scale + v_gap

    # Ensure all bricks are strictly inside the playfield
    for b in grid.all_bricks():
        assert b.rect.left >= pf.left
        assert b.rect.right <= pf.right
        assert b.rect.top >= pf.top
        assert b.rect.bottom <= pf.bottom

    # Ensure grid is centered horizontally within playfield
    first_col_left = grid[0][0].rect.left
    last_col_right = grid[0][cols - 1].rect.right
    # Note: rect coordinates are rounded, so use higher tolerance
    assert pytest.approx((first_col_left + last_col_right) / 2.0, abs=1.0) == pf.center_x


def test_brick_grid_responsive_resizing():
    pf = Playfield(x=100, y=100, width=500, height=400)
    grid = BrickGrid(pf, rows=5, cols=8, margin_x=10, horizontal_gap=4)

    initial_w = grid[0][0].width

    # Resize playfield to larger width
    pf.set_bounds(50, 50, 700, 500)
    grid.recalculate_layout()

    # Bricks must automatically expand to fill available pool width
    new_w = grid[0][0].width
    assert new_w > initial_w

    # Must remain centered in new playfield
    left_x = grid[0][0].x - grid[0][0].width / 2.0
    right_x = grid[0][7].x + grid[0][7].width / 2.0
    assert pytest.approx((left_x + right_x) / 2.0, abs=0.01) == pf.center_x

    # Must remain inside new playfield bounds
    assert left_x >= pf.left
    assert right_x <= pf.right


def test_brick_grid_empty_cells_do_not_shift_remaining_bricks():
    pf = Playfield(x=176, y=236, width=448, height=340)
    grid = BrickGrid(pf, rows=4, cols=4)

    # Capture initial positions
    initial_positions = {(b.row, b.col): (b.x, b.y) for b in grid.all_bricks()}

    # Destroy middle bricks (row 1 col 1 and row 1 col 2)
    grid[1][1].hit()
    grid[1][1].hit()
    grid[1][2].hit()
    grid[1][2].hit()

    assert not grid[1][1].alive
    assert not grid[1][2].alive

    # Alive count reduced
    assert grid.count_alive() == 14
    assert len(grid.alive_bricks()) == 14

    # The destroyed bricks remain in their cells
    assert grid.get_brick(1, 1) is not None
    assert grid.get_brick(1, 2) is not None

    # NO remaining bricks have shifted
    for b in grid.all_bricks():
        assert (b.x, b.y) == initial_positions[(b.row, b.col)]


# ---------------------------------------------------------------------------
# 4. BrickRenderer tests
# ---------------------------------------------------------------------------


def test_brick_renderer_draws_without_error():
    screen = pygame.display.set_mode((800, 600))
    pf = Playfield(x=176, y=236, width=448, height=340)
    grid = BrickGrid(pf, rows=3, cols=4)
    renderer = BrickRenderer()

    # Renders all alive bricks
    renderer.render(screen, grid)

    # Destroy one brick, ensure render succeeds and skips dead brick
    grid[0][0].alive = False
    renderer.render(screen, grid)


def test_brick_renderer_loads_all_colors():
    screen = pygame.display.set_mode((800, 600))
    del screen

    renderer = BrickRenderer()
    for color in BRICK_COLORS:
        surf_normal = renderer.get_brick_surface(color, hp=2, target_width=40)
        assert surf_normal is not None
        assert isinstance(surf_normal, pygame.Surface)
        assert surf_normal.get_width() == 40
        # height will be scaled proportionally, so no strict check needed on it here

        surf_damaged = renderer.get_brick_surface(color, hp=1, target_width=40)
        assert surf_damaged is not None
        assert isinstance(surf_damaged, pygame.Surface)
        assert surf_damaged.get_width() == 40


def test_build_brick_grid_compatibility_helper():
    bricks = build_brick_grid()
    assert len(bricks) == BRICK_GRID_ROWS * BRICK_GRID_COLS
    assert all(isinstance(b, Brick) for b in bricks)
