"""
src/vision/input_processor.py
==============================
Frame pre-processing and MediaPipe Hands landmark extraction.

Uses the MediaPipe Tasks API (mediapipe >= 1.0) with HandLandmarker
in VIDEO running mode for efficient per-frame inference.

Pipeline (per frame):
  BGR frame (from CameraPipeline or direct cv2.VideoCapture)
    |
    +- Optional horizontal flip (mirroring for natural user interaction)
    |
    +- Convert BGR -> RGB        (MediaPipe expects RGB / SRGB)
    |
    +- Wrap in mediapipe.Image(ImageFormat.SRGB, ...)
    |
    +- HandLandmarker.detect_for_video(mp_image, timestamp_ms)
    |
    +- Extract landmark for the configured index (HAND_LANDMARK_INDEX)
         -> normalized (x, y) in [0.0, 1.0] and full 21 joints tuple
         -> or None if no hand detected

Design constraints (see AGENT.md Sec 4 & 5):
  * Output is ONLY normalized coordinates -- never touches game state.
  * Completely decoupled from camera capture -- accepts any generic BGR numpy array.
  * Stateless per call; the caller owns frame lifecycle.
  * MediaPipe model is loaded once in __init__ and reused across frames.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
from mediapipe.tasks.python.vision.core.image import Image, ImageFormat

from src import config

logger = logging.getLogger(__name__)

# Standard MediaPipe Hands 21-landmark skeletal bone connections
HAND_CONNECTIONS: tuple[tuple[int, int], ...] = (
    # Thumb
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    # Index finger
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    # Middle finger
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    # Ring finger
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    # Pinky finger
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    # Palm base
    (0, 17),
)

# Timestamp origin for VIDEO mode (monotonic, milliseconds)
_T0: float = time.monotonic()


def _timestamp_ms() -> int:
    """Return elapsed milliseconds since module load (monotonically increasing)."""
    return int((time.monotonic() - _T0) * 1000)


@dataclass(frozen=True)
class HandLandmark:
    """
    Immutable container for a single extracted hand landmark.

    Attributes
    ----------
    x : float
        Normalised horizontal position in [0.0, 1.0].
        0.0 = left edge of the frame.
    y : float
        Normalised vertical position in [0.0, 1.0].
        0.0 = top edge of the frame.
    handedness : str
        "Left" or "Right" as reported by MediaPipe after horizontal flip
        (so "Right" means the user's physical right hand in mirrored view).
    raw_landmarks : tuple[tuple[float, float, float], ...] | None
        All 21 normalized landmarks (x, y, z) if detected, useful for
        debug rendering, skeleton visualization, and gesture estimation.
    """

    x: float
    y: float
    handedness: str
    raw_landmarks: Optional[tuple[tuple[float, float, float], ...]] = None


class InputProcessor:
    """
    Wraps MediaPipe HandLandmarker (Tasks API) to extract hand landmarks
    from BGR camera frames.

    Decoupled from camera capture:
      Takes any generic BGR numpy frame from CameraPipeline, cv2.VideoCapture,
      or static test images.

    Requires the hand_landmarker.task model bundle to be present at the
    path specified by config.MP_MODEL_PATH (relative to repo root).

    Usage::

        with InputProcessor() as processor:
            while running:
                ret, frame = cap.read()
                if ret:
                    result = processor.process(frame, flip_horizontal=True)
                    if result is not None:
                        paddle_x = result.x   # normalised [0, 1]
    """

    def __init__(
        self,
        model_path: str = config.MP_MODEL_PATH,
        max_num_hands: int = config.MP_MAX_NUM_HANDS,
        min_detection_confidence: float = config.MP_MIN_DETECTION_CONFIDENCE,
        min_presence_confidence: float = config.MP_MIN_PRESENCE_CONFIDENCE,
        min_tracking_confidence: float = config.MP_MIN_TRACKING_CONFIDENCE,
        landmark_index: int = config.HAND_LANDMARK_INDEX,
        flip_horizontal: bool = False,
    ) -> None:
        self._landmark_index = landmark_index
        self._flip_horizontal = flip_horizontal

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        logger.info(
            "InputProcessor initialised (model=%s, max_hands=%d, "
            "det_conf=%.2f, pres_conf=%.2f, track_conf=%.2f, landmark_idx=%d, flip=%s).",
            model_path,
            max_num_hands,
            min_detection_confidence,
            min_presence_confidence,
            min_tracking_confidence,
            landmark_index,
            flip_horizontal,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(
        self,
        frame_bgr: np.ndarray,
        flip_horizontal: Optional[bool] = None,
    ) -> Optional[HandLandmark]:
        """
        Run MediaPipe HandLandmarker on a single BGR frame.

        Parameters
        ----------
        frame_bgr:
            A (H, W, 3) uint8 NumPy array in BGR colour order.
        flip_horizontal:
            Optional override. If True, flips the image horizontally before
            processing. If None, uses the instance's configured default.

        Returns
        -------
        HandLandmark | None
            Normalised landmark coordinates, or None if no hand is
            detected in this frame.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return None

        should_flip = self._flip_horizontal if flip_horizontal is None else flip_horizontal
        if should_flip:
            frame_bgr = cv2.flip(frame_bgr, 1)

        # -- 1. BGR -> RGB -----------------------------------------------
        frame_rgb: np.ndarray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # -- 2. Wrap in MediaPipe Image (SRGB = standard 3-channel RGB) --
        mp_image = Image(image_format=ImageFormat.SRGB, data=frame_rgb)

        # -- 3. Run inference (VIDEO mode needs a monotonic timestamp) ---
        mp_result = self._landmarker.detect_for_video(mp_image, _timestamp_ms())

        # -- 4. Extract landmark -----------------------------------------
        if not mp_result.hand_landmarks:
            return None

        # Use the first detected hand
        hand_landmarks = mp_result.hand_landmarks[0]

        if self._landmark_index >= len(hand_landmarks):
            logger.warning(
                "Landmark index %d out of range (%d landmarks available).",
                self._landmark_index,
                len(hand_landmarks),
            )
            return None

        lm = hand_landmarks[self._landmark_index]

        # Determine handedness label
        handedness_label = "Unknown"
        if mp_result.handedness:
            handedness_label = mp_result.handedness[0][0].display_name

        # Package full 21 landmarks for debug/visualization
        all_landmarks = tuple((float(p.x), float(p.y), float(p.z)) for p in hand_landmarks)

        logger.debug(
            "Landmark[%d] -> x=%.4f  y=%.4f  hand=%s",
            self._landmark_index,
            lm.x,
            lm.y,
            handedness_label,
        )

        return HandLandmark(
            x=float(lm.x),
            y=float(lm.y),
            handedness=handedness_label,
            raw_landmarks=all_landmarks,
        )

    @staticmethod
    def draw_landmarks(
        frame: np.ndarray,
        landmark: HandLandmark,
        highlight_index: int = config.HAND_LANDMARK_INDEX,
        draw_skeleton: bool = True,
    ) -> np.ndarray:
        """
        Draw hand skeleton and key landmark point onto a BGR frame (in-place).

        Parameters
        ----------
        frame:
            (H, W, 3) BGR frame to draw upon.
        landmark:
            HandLandmark containing normalized coordinates and raw_landmarks.
        highlight_index:
            The landmark index to emphasize with a target circle/reticle.
        draw_skeleton:
            Whether to draw the 21 bones and joints if raw_landmarks is available.

        Returns
        -------
        np.ndarray
            The annotated frame.
        """
        h, w = frame.shape[:2]

        # 1. Draw skeleton bones and joints if available
        if draw_skeleton and landmark.raw_landmarks:
            pts: list[tuple[int, int]] = []
            for lx, ly, _ in landmark.raw_landmarks:
                pts.append((int(lx * w), int(ly * h)))

            # Draw bones
            for s, e in HAND_CONNECTIONS:
                if s < len(pts) and e < len(pts):
                    cv2.line(frame, pts[s], pts[e], (0, 220, 255), 2, cv2.LINE_AA)

            # Draw joints
            for px, py in pts:
                cv2.circle(frame, (px, py), 4, (0, 255, 100), -1, cv2.LINE_AA)

        # 2. Highlight control landmark (e.g. index MCP)
        cx = int(landmark.x * w)
        cy = int(landmark.y * h)
        cv2.circle(frame, (cx, cy), 14, (255, 0, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1, cv2.LINE_AA)

        # Label near landmark
        label = f"{landmark.handedness} X:{landmark.x:.2f}"
        cv2.putText(
            frame,
            label,
            (cx + 12, cy - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        return frame

    def close(self) -> None:
        """Release the MediaPipe HandLandmarker resources."""
        self._landmarker.close()
        logger.info("InputProcessor closed.")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "InputProcessor":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
