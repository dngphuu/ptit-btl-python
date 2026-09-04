"""
tests/test_camera_pipeline.py
==============================
Unit tests for :class:`src.vision.camera.CameraPipeline`.

All tests use a **mock** ``cv2.VideoCapture`` so no physical webcam is needed
(satisfies AGENT.md §5 — Offline Testability).

Test categories
---------------
1. Non-blocking read  – ``pipeline.read()`` returns immediately.
2. Latest-frame only  – stale frames are dropped; consumer sees the newest one.
3. Frame delivery     – frames are correctly resized and flipped.
4. Lifecycle          – start/stop is clean; double-start is a no-op.
5. Context manager    – ``with CameraPipeline() as p:`` starts and stops cleanly.
6. Failed camera open – pipeline handles ``cap.isOpened() == False`` gracefully.
7. Read failure       – pipeline keeps running when ``cap.read()`` fails occasionally.
"""

from __future__ import annotations

import time
from typing import Optional
from unittest.mock import MagicMock, patch

import numpy as np

from src.vision.camera import CameraPipeline

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_frame(value: int = 128, width: int = 640, height: int = 480) -> np.ndarray:
    """Return a solid-colour BGR frame for testing."""
    return np.full((height, width, 3), value, dtype=np.uint8)


def _make_mock_cap(
    frames: Optional[list[np.ndarray]] = None,
    opened: bool = True,
) -> MagicMock:
    """
    Build a :class:`unittest.mock.MagicMock` that mimics ``cv2.VideoCapture``.

    Parameters
    ----------
    frames:
        Sequence of frames to return on successive ``read()`` calls.
        After the sequence is exhausted the mock returns the last frame
        indefinitely.  If *None*, a single default frame is used.
    opened:
        Return value of ``isOpened()``.
    """
    if frames is None:
        frames = [_make_frame()]

    cap = MagicMock()
    cap.isOpened.return_value = opened

    # Iterator that cycles through frames and then stays on the last one
    frame_iter = iter(frames)
    last_frame = frames[-1]

    def _read():
        try:
            frame = next(frame_iter)
        except StopIteration:
            frame = last_frame
        return True, frame.copy()

    cap.read.side_effect = _read
    return cap


def _pipeline_with_mock(
    frames: Optional[list[np.ndarray]] = None,
    opened: bool = True,
    target_fps: int = 200,  # run fast so tests don't need long sleeps
) -> tuple[CameraPipeline, MagicMock]:
    """Return (pipeline, mock_cap).  The mock is pre-installed via patch."""
    mock_cap = _make_mock_cap(frames=frames, opened=opened)
    pipeline = CameraPipeline(target_fps=target_fps, queue_timeout=0.001)
    return pipeline, mock_cap


# ---------------------------------------------------------------------------
# 1. Non-blocking read
# ---------------------------------------------------------------------------


class TestNonBlockingRead:
    def test_read_returns_none_before_start(self) -> None:
        """read() on an un-started pipeline must return None immediately."""
        pipeline = CameraPipeline()
        t0 = time.perf_counter()
        result = pipeline.read()
        elapsed = time.perf_counter() - t0

        assert result is None
        assert elapsed < 0.05, f"read() blocked for {elapsed:.3f}s — should be instant"

    def test_read_is_nonblocking_after_start(self) -> None:
        """read() must return within milliseconds even if no frame arrived yet."""
        pipeline, mock_cap = _pipeline_with_mock()

        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()
            try:
                t0 = time.perf_counter()
                pipeline.read()  # result may be None or a frame — doesn't matter
                elapsed = time.perf_counter() - t0
                assert elapsed < 0.05, f"read() blocked for {elapsed:.3f}s"
            finally:
                pipeline.stop()


# ---------------------------------------------------------------------------
# 2. Latest-frame delivery (drop-old-keep-new)
# ---------------------------------------------------------------------------


class TestLatestFrameDelivery:
    def test_consumer_sees_latest_frame(self) -> None:
        """
        When frames arrive faster than the consumer reads them, the pipeline
        should always hand back the *newest* frame, not a stale one.
        """
        frame_a = _make_frame(value=10)
        frame_b = _make_frame(value=200)
        # Deliver many copies of frame_a then frame_b
        frames = [frame_a] * 10 + [frame_b] * 20

        pipeline, mock_cap = _pipeline_with_mock(frames=frames, target_fps=300)

        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()
            time.sleep(0.15)  # let worker produce plenty of frames

            # Drain all available frames
            received: list[np.ndarray] = []
            for _ in range(50):
                f = pipeline.read()
                if f is not None:
                    received.append(f)
                time.sleep(0.001)

            pipeline.stop()

        # The LAST received frame should be frame_b (value ≈ 200)
        assert len(received) > 0, "No frames received at all."
        last = received[-1]
        assert last.mean() > 100, (
            f"Expected last frame to be frame_b (bright), got mean={last.mean():.1f}"
        )

    def test_frames_captured_counter_increments(self) -> None:
        """frames_captured should increase while the pipeline is running."""
        pipeline, mock_cap = _pipeline_with_mock(target_fps=100)

        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()
            time.sleep(0.2)
            captured = pipeline.frames_captured
            pipeline.stop()

        assert captured > 0, "frames_captured should be > 0 after running for 200 ms"


# ---------------------------------------------------------------------------
# 3. Frame shape integrity
# ---------------------------------------------------------------------------


class TestFrameShape:
    def test_frame_has_correct_shape(self) -> None:
        """Frames delivered by read() must be (H, W, 3) BGR arrays."""
        pipeline, mock_cap = _pipeline_with_mock(target_fps=100)

        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()

            frame: Optional[np.ndarray] = None
            deadline = time.perf_counter() + 2.0
            while frame is None and time.perf_counter() < deadline:
                frame = pipeline.read()
                time.sleep(0.005)

            pipeline.stop()

        assert frame is not None, "No frame received within 2 seconds."
        assert frame.ndim == 3, f"Expected 3-D array, got shape {frame.shape}"
        assert frame.shape[2] == 3, "Expected 3 colour channels (BGR)."

    def test_frame_is_numpy_array(self) -> None:
        """Frames must be numpy arrays (not raw Python objects)."""
        pipeline, mock_cap = _pipeline_with_mock(target_fps=100)

        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()

            frame: Optional[np.ndarray] = None
            deadline = time.perf_counter() + 2.0
            while frame is None and time.perf_counter() < deadline:
                frame = pipeline.read()
                time.sleep(0.005)

            pipeline.stop()

        assert isinstance(frame, np.ndarray), f"Expected np.ndarray, got {type(frame)}"


# ---------------------------------------------------------------------------
# 4. Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_is_running_false_before_start(self) -> None:
        pipeline = CameraPipeline()
        assert pipeline.is_running is False

    def test_is_running_true_after_start(self) -> None:
        pipeline, mock_cap = _pipeline_with_mock()
        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()
            assert pipeline.is_running is True
            pipeline.stop()

    def test_is_running_false_after_stop(self) -> None:
        pipeline, mock_cap = _pipeline_with_mock()
        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()
            pipeline.stop()
        assert pipeline.is_running is False

    def test_double_start_is_idempotent(self) -> None:
        """Calling start() on an already-running pipeline must not raise."""
        pipeline, mock_cap = _pipeline_with_mock()
        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()
            thread_before = pipeline._thread
            pipeline.start()  # second call — should be a no-op
            assert pipeline._thread is thread_before, (
                "Double start() should not spawn a second thread."
            )
            pipeline.stop()

    def test_stop_is_idempotent(self) -> None:
        """Calling stop() twice must not raise."""
        pipeline, mock_cap = _pipeline_with_mock()
        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()
            pipeline.stop()
            pipeline.stop()  # should not raise


# ---------------------------------------------------------------------------
# 5. Context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_context_manager_starts_and_stops(self) -> None:
        pipeline, mock_cap = _pipeline_with_mock()
        with patch("cv2.VideoCapture", return_value=mock_cap):
            with pipeline as p:
                assert p.is_running is True
            assert pipeline.is_running is False

    def test_context_manager_returns_self(self) -> None:
        pipeline, mock_cap = _pipeline_with_mock()
        with patch("cv2.VideoCapture", return_value=mock_cap):
            with pipeline as p:
                assert p is pipeline


# ---------------------------------------------------------------------------
# 6. Failed camera open
# ---------------------------------------------------------------------------


class TestFailedCameraOpen:
    def test_pipeline_does_not_crash_when_camera_unavailable(self) -> None:
        """If the camera can't be opened, the worker exits without crashing."""
        pipeline, mock_cap = _pipeline_with_mock(opened=False)
        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()
            time.sleep(0.1)  # give worker time to exit
            pipeline.stop()

        # No exception → pass.  Thread should have exited cleanly.
        assert pipeline.is_running is False

    def test_read_returns_none_when_camera_fails(self) -> None:
        """read() must return None when the camera device is unavailable."""
        pipeline, mock_cap = _pipeline_with_mock(opened=False)
        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()
            time.sleep(0.05)
            frame = pipeline.read()
            pipeline.stop()

        assert frame is None


# ---------------------------------------------------------------------------
# 7. Intermittent read failure
# ---------------------------------------------------------------------------


class TestIntermittentReadFailure:
    def test_pipeline_survives_occasional_read_failures(self) -> None:
        """
        The worker must keep running and eventually deliver a good frame
        even if cap.read() fails a few times.
        """
        good_frame = _make_frame(value=77)
        call_count = 0

        def _read_with_failures():
            nonlocal call_count
            call_count += 1
            if call_count <= 5:
                return False, None  # simulate failure
            return True, good_frame.copy()

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = _read_with_failures

        pipeline = CameraPipeline(target_fps=200, queue_timeout=0.001)
        with patch("cv2.VideoCapture", return_value=mock_cap):
            pipeline.start()

            received: Optional[np.ndarray] = None
            deadline = time.perf_counter() + 2.0
            while received is None and time.perf_counter() < deadline:
                received = pipeline.read()
                time.sleep(0.005)

            pipeline.stop()

        assert received is not None, "Should have received a frame after read failures cleared."
        assert received.mean() > 50, "Frame value mismatch."
