"""
tests/test_filters.py
=====================
Unit tests for coordinate smoothing filters (EMAFilter, lerp, smooth_coordinate).
"""

from __future__ import annotations

import numpy as np
import pytest

from src import config
from src.filters import EMAFilter, lerp, smooth_coordinate


class TestEMAFilterInitialization:
    def test_default_alpha(self) -> None:
        filt = EMAFilter()
        assert filt.alpha == config.EMA_ALPHA
        assert filt.value is None
        assert not filt.is_initialized

    def test_custom_alpha(self) -> None:
        filt = EMAFilter(alpha=0.15)
        assert filt.alpha == pytest.approx(0.15)

    def test_initial_value_set(self) -> None:
        filt = EMAFilter(initial_value=0.5)
        assert filt.value == pytest.approx(0.5)
        assert filt.is_initialized

    @pytest.mark.parametrize("invalid_alpha", [0.0, -0.1, 1.1, 2.0, -10.0])
    def test_invalid_alpha_raises_value_error(self, invalid_alpha: float) -> None:
        with pytest.raises(ValueError, match="alpha must be in range"):
            EMAFilter(alpha=invalid_alpha)

    @pytest.mark.parametrize("invalid_alpha", [0.0, -0.5, 1.05])
    def test_invalid_alpha_setter_raises_value_error(self, invalid_alpha: float) -> None:
        filt = EMAFilter(alpha=0.3)
        with pytest.raises(ValueError, match="alpha must be in range"):
            filt.alpha = invalid_alpha


class TestEMAFilterBehavior:
    def test_first_update_initializes_immediately(self) -> None:
        """First measurement should set the value directly without lag from 0."""
        filt = EMAFilter(alpha=0.2)
        assert filt.value is None
        val = filt.update(0.75)
        assert val == pytest.approx(0.75)
        assert filt.value == pytest.approx(0.75)
        assert filt.is_initialized

    def test_filter_and_call_aliases(self) -> None:
        """filter() and __call__() should behave identically to update()."""
        filt1 = EMAFilter(alpha=0.3)
        filt2 = EMAFilter(alpha=0.3)
        filt3 = EMAFilter(alpha=0.3)
        filt4 = EMAFilter(alpha=0.3)

        assert filt1.update(0.4) == pytest.approx(filt2.filter(0.4))
        assert filt1.update(0.8) == pytest.approx(filt2.filter(0.8))

        assert filt3(0.4) == pytest.approx(filt4.update(0.4))
        assert filt3(0.8) == pytest.approx(filt4.update(0.8))

    def test_subsequent_ema_formula(self) -> None:
        """Check exact mathematical values for sequential updates."""
        alpha = 0.4
        filt = EMAFilter(alpha=alpha)
        # Step 1: initial value
        s0 = filt.update(1.0)
        assert s0 == pytest.approx(1.0)

        # Step 2: 0.4 * 2.0 + 0.6 * 1.0 = 0.8 + 0.6 = 1.4
        s1 = filt.update(2.0)
        assert s1 == pytest.approx(1.4)

        # Step 3: 0.4 * 0.0 + 0.6 * 1.4 = 0.84
        s2 = filt.update(0.0)
        assert s2 == pytest.approx(0.84)

    def test_convergence_to_constant(self) -> None:
        """A series of constant inputs must asymptotically converge to that constant."""
        filt = EMAFilter(alpha=0.25)
        filt.update(0.0)
        for _ in range(50):
            val = filt.update(10.0)
        assert val == pytest.approx(10.0, abs=1e-4)

    def test_jitter_reduction(self) -> None:
        """
        Verify that EMA filtering significantly reduces high-frequency jitter.
        The variance of a noisy signal should decrease markedly after filtering.
        """
        np.random.seed(42)
        true_signal = 0.5
        noise = np.random.normal(0, 0.05, size=200)
        noisy_signal = true_signal + noise

        filt = EMAFilter(alpha=0.2)
        smoothed = [filt.update(float(x)) for x in noisy_signal]

        # Ignore the first few samples for steady-state variance
        raw_std = np.std(noisy_signal[10:])
        smoothed_std = np.std(smoothed[10:])

        assert smoothed_std < raw_std * 0.6, (
            f"Expected significant jitter reduction: raw std={raw_std:.4f}, "
            f"smoothed std={smoothed_std:.4f}"
        )

    def test_reset_uninitialized(self) -> None:
        filt = EMAFilter(alpha=0.3)
        filt.update(0.5)
        assert filt.is_initialized

        filt.reset()
        assert not filt.is_initialized
        assert filt.value is None

        # Next update behaves like initial
        assert filt.update(0.9) == pytest.approx(0.9)

    def test_reset_with_explicit_value(self) -> None:
        filt = EMAFilter(alpha=0.3)
        filt.update(0.5)
        filt.reset(value=0.2)
        assert filt.is_initialized
        assert filt.value == pytest.approx(0.2)

        # Next update blends with explicit reset value
        # 0.3 * 1.0 + 0.7 * 0.2 = 0.3 + 0.14 = 0.44
        assert filt.update(1.0) == pytest.approx(0.44)


class TestLerpAndSmoothCoordinate:
    def test_lerp_endpoints(self) -> None:
        assert lerp(10.0, 20.0, 0.0) == pytest.approx(10.0)
        assert lerp(10.0, 20.0, 1.0) == pytest.approx(20.0)
        assert lerp(10.0, 20.0, 0.5) == pytest.approx(15.0)

    def test_lerp_extrapolation(self) -> None:
        assert lerp(0.0, 10.0, 1.5) == pytest.approx(15.0)
        assert lerp(0.0, 10.0, -0.5) == pytest.approx(-5.0)

    def test_smooth_coordinate_formula(self) -> None:
        # alpha * curr + (1 - alpha) * prev
        # 0.3 * 1.0 + 0.7 * 0.0 = 0.3
        assert smooth_coordinate(1.0, 0.0, alpha=0.3) == pytest.approx(0.3)
        # 0.5 * 2.0 + 0.5 * 4.0 = 3.0
        assert smooth_coordinate(2.0, 4.0, alpha=0.5) == pytest.approx(3.0)
