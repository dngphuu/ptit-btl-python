"""
src/ui/nine_slice.py
====================
9-slice panel renderer using the Kenney Pixel Adventure UI tileset.

Tile layout (13 cols x 7 rows, 32x32 px each, 1px spacing in packed sheet):
Row 0, cols 0-2  -> top-left / top-mid / top-right corner & edge tiles
Row 1, cols 0-2  -> mid-left / mid-center(fill) / mid-right
Row 2, cols 0-2  -> bot-left / bot-mid / bot-right

Tile index formula (no spacing, individual PNG files):
  idx = row * 13 + col
  e.g. top-left=0, top-mid=1, top-right=2
       mid-left=13, mid-fill=14, mid-right=15
       bot-left=26, bot-mid=27, bot-right=28
"""

from __future__ import annotations

import pygame

TILE_SIZE: int = 32  # native px of each Kenney tile

# 9-slice tile indices (13-column grid, zero-based row/col)
_IDX: dict[str, int] = {
    "tl": 0,
    "tm": 1,
    "tr": 2,
    "ml": 13,
    "mm": 14,
    "mr": 15,
    "bl": 26,
    "bm": 27,
    "br": 28,
}


class NineSlicePanel:
    """Renders a scalable panel by compositing 9 tile sprites."""

    def __init__(self, tile_dir: str, scale: int = 2) -> None:
        """
        Parameters
        ----------
        tile_dir : str
            Directory containing tile_0000.png … tile_0090.png.
        scale : int
            Integer upscale applied to each 32-px tile (default 2 -> 64 px).
        """
        self._ts = TILE_SIZE * scale
        self._tiles: dict[str, pygame.Surface] = {}
        for name, idx in _IDX.items():
            raw = pygame.image.load(f"{tile_dir}/tile_{idx:04d}.png").convert_alpha()
            self._tiles[name] = pygame.transform.scale(raw, (self._ts, self._ts))

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Blit a 9-slice panel that exactly fills *rect*."""
        ts = self._ts
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        iw = max(w - 2 * ts, 0)  # inner width
        ih = max(h - 2 * ts, 0)  # inner height

        t = self._tiles

        # corners
        surface.blit(t["tl"], (x, y))
        surface.blit(t["tr"], (x + w - ts, y))
        surface.blit(t["bl"], (x, y + h - ts))
        surface.blit(t["br"], (x + w - ts, y + h - ts))

        # horizontal edges (stretched)
        if iw > 0:
            surface.blit(pygame.transform.scale(t["tm"], (iw, ts)), (x + ts, y))
            surface.blit(pygame.transform.scale(t["bm"], (iw, ts)), (x + ts, y + h - ts))

        # vertical edges (stretched)
        if ih > 0:
            surface.blit(pygame.transform.scale(t["ml"], (ts, ih)), (x, y + ts))
            surface.blit(pygame.transform.scale(t["mr"], (ts, ih)), (x + w - ts, y + ts))

        # fill
        if iw > 0 and ih > 0:
            surface.blit(pygame.transform.scale(t["mm"], (iw, ih)), (x + ts, y + ts))
