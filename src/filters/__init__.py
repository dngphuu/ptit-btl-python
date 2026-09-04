"""
src/filters
===========
Coordinate smoothing and signal filtering algorithms for game controls.
"""

from __future__ import annotations

from src.filters.ema import EMAFilter, lerp, smooth_coordinate

__all__ = ["EMAFilter", "lerp", "smooth_coordinate"]
