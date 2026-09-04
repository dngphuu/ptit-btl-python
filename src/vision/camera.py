"""
src/vision/camera.py
====================
Non-blocking camera capture pipeline.

Design goals (see AGENT.md §5):
  • The game render thread must **never** block on frame capture.
  • Always deliver the **latest** frame — drop stale frames rather than queue them.
  • The pipeline must start / stop cleanly and be safe to call from any thread.

Implementation:
  ┌──────────────────────────────────────────────────────────┐
  │  Daemon worker thread                                     │
  │    cv2.VideoCapture.read() → resize → put to queue       │
  │                        (blocks only inside the thread)    │
  └────────────────────────┬─────────────────────────────────┘
                           │  queue.Queue(maxsize=1)
                           │  (old frame dropped when full)
  ┌────────────────────────▼─────────────────────────────────┐
  │  Game / consumer thread                                   │
  │    pipeline.read() → returns latest BGR frame or None    │
  └──────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Optional

import cv2
import numpy as np

from src import config

logger = logging.getLogger(__name__)


class CameraPipeline:
    """
    Thread-safe, non-blocking webcam capture pipeline.

    Usage::

        pipeline = CameraPipeline()
        pipeline.start()

        while running:
            frame = pipeline.read()   # None if no frame yet
            if frame is not None:
                process(frame)

        pipeline.stop()

    The pipeline can also be used as a context manager::

        with CameraPipeline() as pipeline:
            frame = pipeline.read()
    """

    def __init__(
        self,
        camera_index: int = config.CAMERA_INDEX,
        width: int = config.CAMERA_WIDTH,
        height: int = config.CAMERA_HEIGHT,
        target_fps: int = config.CAMERA_TARGET_FPS,
        queue_maxsize: int = config.CAMERA_QUEUE_MAXSIZE,
        queue_timeout: float = config.CAMERA_QUEUE_TIMEOUT,
        backend: int = cv2.CAP_DSHOW,
    ) -> None:
        self._camera_index = camera_index
        self._width = width
        self._height = height
        self._target_fps = target_fps
        self._queue_timeout = queue_timeout
        # CAP_DSHOW (DirectShow) is far more reliable than the default MSMF
        # backend on Windows — MSMF can silently return no frames even after
        # isOpened() returns True.  On non-Windows platforms pass cv2.CAP_ANY.
        self._backend = backend

        # maxsize=1 → producer drops stale frames, consumer always gets fresh
        self._frame_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=queue_maxsize)

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None

        # Runtime diagnostics
        self._frames_captured: int = 0
        self._frames_dropped: int = 0
        self._actual_fps: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> "CameraPipeline":
        """Open the camera and launch the background capture thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("CameraPipeline.start() called while already running.")
            return self

        self._stop_event.clear()
        self._frames_captured = 0
        self._frames_dropped = 0

        self._thread = threading.Thread(
            target=self._worker,
            name="CameraCaptureThread",
            daemon=True,  # dies automatically when the main process exits
        )
        self._thread.start()
        logger.info("CameraPipeline started (device=%d).", self._camera_index)
        return self

    def stop(self) -> None:
        """Signal the worker thread to stop and wait for it to exit."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            if self._thread.is_alive():
                logger.warning("CameraCaptureThread did not exit within timeout.")
        self._thread = None
        logger.info(
            "CameraPipeline stopped. captured=%d, dropped=%d, fps=%.1f",
            self._frames_captured,
            self._frames_dropped,
            self._actual_fps,
        )

    def read(self) -> Optional[np.ndarray]:
        """
        Return the most recent BGR frame, or ``None`` if none is available yet.

        This call is **non-blocking** — it never waits for the camera thread.
        """
        try:
            return self._frame_queue.get_nowait()
        except queue.Empty:
            return None

    @property
    def is_running(self) -> bool:
        """True while the background capture thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    @property
    def frames_captured(self) -> int:
        return self._frames_captured

    @property
    def frames_dropped(self) -> int:
        return self._frames_dropped

    @property
    def actual_fps(self) -> float:
        return self._actual_fps

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "CameraPipeline":
        return self.start()

    def __exit__(self, *_: object) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Internal worker (runs in daemon thread)
    # ------------------------------------------------------------------

    def _worker(self) -> None:
        """
        Capture loop running entirely in the background thread.

        Strategy for zero-lag delivery:
          1. Read frame from OpenCV (blocking inside this thread — OK).
          2. Resize to the configured resolution.
          3. Try to put the frame into the queue:
             - If the queue is full (consumer hasn't picked up yet), drain the
               old frame first, then insert the new one.  This ensures the
               consumer always sees the *latest* frame, never a stale one.
        """
        cap = cv2.VideoCapture(self._camera_index, self._backend)
        if not cap.isOpened():
            logger.error(
                "Cannot open camera device %d. "
                "Check that a webcam is connected and not in use by another application.",
                self._camera_index,
            )
            return

        # Apply preferred resolution / FPS hints (best-effort; driver may override)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        cap.set(cv2.CAP_PROP_FPS, self._target_fps)

        self._cap = cap
        frame_interval = 1.0 / max(self._target_fps, 1)
        fps_window_start = time.perf_counter()
        fps_window_count = 0

        try:
            while not self._stop_event.is_set():
                loop_start = time.perf_counter()

                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning("Camera read failed — retrying.")
                    time.sleep(0.01)
                    continue

                # Resize to the canonical resolution (in case driver returns different size)
                if frame.shape[1] != self._width or frame.shape[0] != self._height:
                    frame = cv2.resize(frame, (self._width, self._height))

                # Flip horizontally so the image is mirrored (natural for the user)
                frame = cv2.flip(frame, 1)

                self._frames_captured += 1
                fps_window_count += 1

                # Put into queue — drop the oldest frame if the consumer is slow
                try:
                    self._frame_queue.put(frame, timeout=self._queue_timeout)
                except queue.Full:
                    # Drain the stale frame and replace with the fresh one
                    try:
                        self._frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        self._frame_queue.put_nowait(frame)
                    except queue.Full:
                        pass
                    self._frames_dropped += 1

                # Update rolling FPS counter every second
                elapsed = time.perf_counter() - fps_window_start
                if elapsed >= 1.0:
                    self._actual_fps = fps_window_count / elapsed
                    fps_window_count = 0
                    fps_window_start = time.perf_counter()

                # Throttle to target FPS (avoid pegging the CPU)
                processing_time = time.perf_counter() - loop_start
                sleep_time = frame_interval - processing_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

        finally:
            cap.release()
            self._cap = None
            logger.info("Camera device released.")
