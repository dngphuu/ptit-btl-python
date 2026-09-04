"""
src/filters/ema.py
==================
Exponential Moving Average (EMA) and linear interpolation smoothing filters.

Used for eliminating high-frequency sensor noise and camera landmark jitter
while maintaining low latency for responsive game control.
"""

from __future__ import annotations

from typing import Optional

from src import config


def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation between `a` and `b` by factor `t`.

    Parameters
    ----------
    a : float
        Start value (when t = 0).
    b : float
        Target value (when t = 1).
    t : float
        Interpolation factor, typically in [0.0, 1.0].

    Returns
    -------
    float
        Interpolated value: (1 - t) * a + t * b
    """
    return (1.0 - t) * a + t * b


def smooth_coordinate(
    current_val: float, prev_val: float, alpha: float = config.EMA_ALPHA
) -> float:
    """
    Single-step Exponential Moving Average calculation.

    Parameters
    ----------
    current_val : float
        The new raw coordinate measurement.
    prev_val : float
        The previous smoothed coordinate.
    alpha : float
        Smoothing coefficient in (0.0, 1.0].
        Higher value = faster response, less smoothing.
        Lower value = smoother movement, slightly more latency.

    Returns
    -------
    float
        Smoothed coordinate.
    """
    return alpha * current_val + (1.0 - alpha) * prev_val


class EMAFilter:
    """
    Exponential Moving Average (EMA) 1D signal filter.

    Formula:
        S_t = alpha * Y_t + (1 - alpha) * S_{t-1}

    Key behaviors:
    - First measurement immediately initializes the filter state, avoiding
      startup drift/lag from zero.
    - Preserves state across calls until explicitly reset.
    - Zero-overhead state updates suitable for 60+ FPS game loops.

    Parameters
    ----------
    alpha : float
        Smoothing factor in range (0.0, 1.0]. Defaults to config.EMA_ALPHA.
    initial_value : float | None
        Optional preset value. If None, the first update() sets the state directly.
    """

    def __init__(
        self,
        alpha: float = config.EMA_ALPHA,
        initial_value: Optional[float] = None,
    ) -> None:
        if not (0.0 < alpha <= 1.0):
            raise ValueError(f"alpha must be in range (0.0, 1.0], got {alpha}")
        self._alpha: float = alpha
        self._value: Optional[float] = float(initial_value) if initial_value is not None else None

    @property
    def alpha(self) -> float:
        """Smoothing coefficient."""
        return self._alpha

    @alpha.setter
    def alpha(self, val: float) -> None:
        if not (0.0 < val <= 1.0):
            raise ValueError(f"alpha must be in range (0.0, 1.0], got {val}")
        self._alpha = val

    @property
    def value(self) -> Optional[float]:
        """Current smoothed value, or None if no updates have been processed."""
        return self._value

    @property
    def is_initialized(self) -> bool:
        """True if the filter has received at least one sample."""
        return self._value is not None

    def update(self, measurement: float) -> float:
        """
        Incorporate a new raw measurement and return the updated smoothed value.

        Parameters
        ----------
        measurement : float
            Raw input coordinate / value.

        Returns
        -------
        float
            Smoothed value.
        """
        val = float(measurement)
        if self._value is None:
            self._value = val
        else:
            self._value = self._alpha * val + (1.0 - self._alpha) * self._value
        return self._value

    def filter(self, measurement: float) -> float:
        """Alias for `update`."""
        return self.update(measurement)

    def __call__(self, measurement: float) -> float:
        """Allow calling the filter instance as a function."""
        return self.update(measurement)

    def reset(self, value: Optional[float] = None) -> None:
        """
        Reset the filter state.

        Parameters
        ----------
        value : float | None
            Optional new state. If None, filter resets to uninitialized state.
        """
        self._value = float(value) if value is not None else None
