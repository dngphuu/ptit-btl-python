"""
tests/test_input_processor.py
==============================
Dual-mode test file for InputProcessor:

1. Offline automated tests (runs with pytest):
       uv run pytest tests/test_input_processor.py -v
   Uses synthetic NumPy frames and mocks HandLandmarker so it requires
   no webcam and no external model download.

2. Interactive live webcam test (runs directly):
       uv run python tests/test_input_processor.py
       uv run python tests/test_input_processor.py --camera 0 --width 640 --height 480

   Opens your real webcam, tracks your hand in real time, displays
   the 21-joint skeletal tracking, tracked landmark coordinates, and an
   interactive preview of the paddle movement. Fully decoupled so it runs
   standalone on the mediapipe-hand branch even without CameraPipeline.
"""

from __future__ import annotations

import argparse
import sys
import time
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from src import config
from src.filters import EMAFilter
from src.vision.input_processor import (
    HandLandmark,
    InputProcessor,
)

# ---------------------------------------------------------------------------
# Helpers for automated unit tests
# ---------------------------------------------------------------------------


def _make_frame(h: int = 480, w: int = 640) -> np.ndarray:
    """Return a solid-colour uint8 BGR frame."""
    return np.zeros((h, w, 3), dtype=np.uint8)


def _mock_lm(x: float = 0.5, y: float = 0.4, z: float = 0.0) -> MagicMock:
    """Build a minimal MediaPipe NormalizedLandmark-style mock."""
    lm = MagicMock()
    lm.x = x
    lm.y = y
    lm.z = z
    return lm


def _mp_result(
    landmark_x: float = 0.5,
    landmark_y: float = 0.4,
    handedness: str = "Right",
    num_landmarks: int = 21,
) -> MagicMock:
    """Build a realistic HandLandmarkerResult mock."""
    result = MagicMock()
    landmarks = [_mock_lm(0.0, 0.0) for _ in range(num_landmarks)]
    landmarks[5] = _mock_lm(landmark_x, landmark_y)
    result.hand_landmarks = [landmarks]

    cls_mock = MagicMock()
    cls_mock.display_name = handedness
    handedness_group = MagicMock()
    handedness_group.__getitem__ = lambda self, i: cls_mock
    result.handedness = [handedness_group]

    return result


def _mp_result_no_hand() -> MagicMock:
    result = MagicMock()
    result.hand_landmarks = []
    result.handedness = []
    return result


_PATCH_LANDMARKER = "src.vision.input_processor.HandLandmarker"


# ---------------------------------------------------------------------------
# Pytest Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def processor():
    """InputProcessor with HandLandmarker.create_from_options mocked out."""
    with patch(_PATCH_LANDMARKER) as MockHL:
        mock_instance = MockHL.create_from_options.return_value
        proc = InputProcessor.__new__(InputProcessor)
        proc._landmark_index = 5
        proc._flip_horizontal = False
        proc._landmarker = mock_instance
        yield proc, mock_instance


# ---------------------------------------------------------------------------
# Tests -- HandLandmark dataclass
# ---------------------------------------------------------------------------


class TestHandLandmarkDataclass:
    def test_immutable(self):
        lm = HandLandmark(x=0.3, y=0.7, handedness="Right")
        with pytest.raises(Exception):
            lm.x = 0.5  # type: ignore[misc]

    def test_fields(self):
        lm = HandLandmark(x=0.1, y=0.9, handedness="Left")
        assert lm.x == pytest.approx(0.1)
        assert lm.y == pytest.approx(0.9)
        assert lm.handedness == "Left"
        assert lm.raw_landmarks is None

    def test_raw_landmarks_tuple(self):
        raw = ((0.1, 0.2, 0.0), (0.3, 0.4, 0.0))
        lm = HandLandmark(x=0.1, y=0.2, handedness="Right", raw_landmarks=raw)
        assert lm.raw_landmarks == raw


# ---------------------------------------------------------------------------
# Tests -- InputProcessor.process()
# ---------------------------------------------------------------------------


class TestInputProcessorProcess:
    def test_returns_none_for_none_frame(self, processor):
        proc, _ = processor
        assert proc.process(None) is None  # type: ignore[arg-type]

    def test_returns_none_for_empty_frame(self, processor):
        proc, _ = processor
        assert proc.process(np.array([])) is None

    def test_returns_none_when_no_hand_detected(self, processor):
        proc, mock_landmarker = processor
        mock_landmarker.detect_for_video.return_value = _mp_result_no_hand()
        result = proc.process(_make_frame())
        assert result is None

    def test_returns_landmark_when_hand_detected(self, processor):
        proc, mock_landmarker = processor
        mock_landmarker.detect_for_video.return_value = _mp_result(
            landmark_x=0.55, landmark_y=0.35, handedness="Right"
        )
        result = proc.process(_make_frame())
        assert result is not None
        assert result.x == pytest.approx(0.55)
        assert result.y == pytest.approx(0.35)
        assert result.handedness == "Right"
        assert result.raw_landmarks is not None
        assert len(result.raw_landmarks) == 21

    def test_bgr_to_rgb_conversion_applied(self, processor):
        proc, mock_landmarker = processor
        mock_landmarker.detect_for_video.return_value = _mp_result_no_hand()

        with patch("src.vision.input_processor.Image") as MockImage:
            MockImage.return_value = MagicMock()
            bgr_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            bgr_frame[:, :, 0] = 255  # Blue channel set in BGR

            proc.process(bgr_frame)

            call_kwargs = MockImage.call_args
            passed_data: np.ndarray | None = call_kwargs.kwargs.get("data")
            if passed_data is None:
                passed_data = call_kwargs[1].get("data")
            if passed_data is None and call_kwargs[0]:
                passed_data = call_kwargs[0][1]
            assert passed_data is not None, "Image() was not called with data"
            assert passed_data[0, 0, 2] == 255, (
                "Blue BGR channel should appear as red (index 2) after BGR->RGB conversion"
            )

    def test_flip_horizontal_applied_when_requested(self, processor):
        proc, mock_landmarker = processor
        mock_landmarker.detect_for_video.return_value = _mp_result_no_hand()

        with patch("src.vision.input_processor.Image") as MockImage:
            MockImage.return_value = MagicMock()
            bgr_frame = np.zeros((10, 10, 3), dtype=np.uint8)
            bgr_frame[:, :3, :] = 200  # Left 3 columns bright

            # Process with flip_horizontal=True
            proc.process(bgr_frame, flip_horizontal=True)

            call_kwargs = MockImage.call_args
            passed_data: np.ndarray = (
                call_kwargs.kwargs.get("data")
                if "data" in call_kwargs.kwargs
                else call_kwargs[0][1]
            )
            # After horizontal flip, the right 3 columns should now be bright
            assert np.all(passed_data[:, -3:, :] == 200)

    def test_landmark_index_oob_returns_none(self, processor):
        proc, mock_landmarker = processor
        result_mock = MagicMock()
        result_mock.hand_landmarks = [[_mock_lm()] * 3]
        result_mock.handedness = []
        mock_landmarker.detect_for_video.return_value = result_mock

        assert proc.process(_make_frame()) is None

    def test_handedness_unknown_when_list_empty(self, processor):
        proc, mock_landmarker = processor
        result_mock = MagicMock()
        result_mock.hand_landmarks = [[_mock_lm()] * 21]
        result_mock.handedness = []
        mock_landmarker.detect_for_video.return_value = result_mock

        result = proc.process(_make_frame())
        assert result is not None
        assert result.handedness == "Unknown"

    def test_detect_for_video_called_with_increasing_timestamps(self, processor):
        proc, mock_landmarker = processor
        mock_landmarker.detect_for_video.return_value = _mp_result_no_hand()

        proc.process(_make_frame())
        proc.process(_make_frame())

        assert mock_landmarker.detect_for_video.call_count == 2
        ts1 = mock_landmarker.detect_for_video.call_args_list[0][0][1]
        ts2 = mock_landmarker.detect_for_video.call_args_list[1][0][1]
        assert ts2 >= ts1

    def test_draw_landmarks_annotates_frame(self):
        raw = tuple((0.5, 0.5, 0.0) for _ in range(21))
        landmark = HandLandmark(x=0.5, y=0.5, handedness="Right", raw_landmarks=raw)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        annotated = InputProcessor.draw_landmarks(frame, landmark)
        assert annotated.shape == (480, 640, 3)
        # Should have drawn non-zero pixel values
        assert np.count_nonzero(annotated) > 0


# ---------------------------------------------------------------------------
# Tests -- InputProcessor lifecycle
# ---------------------------------------------------------------------------


class TestInputProcessorLifecycle:
    def test_context_manager_calls_close(self):
        with patch(_PATCH_LANDMARKER) as MockHL:
            mock_instance = MockHL.create_from_options.return_value
            with InputProcessor.__new__(InputProcessor) as proc:
                proc._landmarker = mock_instance
            mock_instance.close.assert_called_once()

    def test_close_releases_landmarker(self):
        with patch(_PATCH_LANDMARKER) as MockHL:
            mock_instance = MockHL.create_from_options.return_value
            proc = InputProcessor.__new__(InputProcessor)
            proc._landmarker = mock_instance
            proc.close()
            mock_instance.close.assert_called_once()


# ---------------------------------------------------------------------------
# CLI Argument Parser for Live Mode
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Live Camera Hand Tracking Test for InputProcessor"
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=config.CAMERA_INDEX,
        help="Camera device index (default: %(default)s)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=config.CAMERA_WIDTH,
        help="Frame width (default: %(default)s)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=config.CAMERA_HEIGHT,
        help="Frame height (default: %(default)s)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=config.CAMERA_TARGET_FPS,
        help="Desired camera FPS (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=config.MP_MODEL_PATH,
        help="Path to hand_landmarker.task model (default: %(default)s)",
    )
    parser.add_argument(
        "--landmark",
        type=int,
        default=config.HAND_LANDMARK_INDEX,
        help="Target landmark index for paddle control (default: %(default)s, index MCP=5)",
    )
    parser.add_argument(
        "--no-flip",
        action="store_true",
        help="Disable horizontal flip (default is flipped for mirror view)",
    )
    parser.add_argument(
        "--use-pipeline",
        action="store_true",
        help="Use CameraPipeline if available instead of direct cv2.VideoCapture",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=config.EMA_ALPHA,
        help="EMA smoothing factor alpha in (0, 1] (default: %(default)s)",
    )
    parser.add_argument(
        "--no-ema",
        action="store_true",
        help="Disable EMA smoothing (compare raw vs smoothed)",
    )
    return parser


# ---------------------------------------------------------------------------
# Interactive Live Camera Test Runner
# ---------------------------------------------------------------------------


def run_live_camera(args: argparse.Namespace) -> None:
    """
    Run interactive real camera hand tracking test with OpenCV display.
    """
    print("=" * 65)
    print("  VisionBrick: Live Hand Tracking & Input Processor Test")
    print("=" * 65)
    print(f"  Camera Device  : {args.camera}")
    print(f"  Resolution     : {args.width}x{args.height}")
    print(f"  Target FPS     : {args.fps}")
    print(f"  Model Asset    : {args.model}")
    print(f"  Track Landmark : Index #{args.landmark}")
    ema_info = "Disabled" if args.no_ema else f"Enabled (alpha={args.alpha:.2f})"
    print(f"  EMA Smoothing  : {ema_info}")
    print("  Controls       : [Q/ESC] Quit | [F] Flip | [E] Toggle EMA | [+/-] Tune Alpha")
    print("=" * 65)

    # Initialize InputProcessor
    try:
        processor = InputProcessor(
            model_path=args.model,
            landmark_index=args.landmark,
            flip_horizontal=not args.no_flip,
        )
    except Exception as exc:
        print(f"\n❌ Failed to initialize InputProcessor: {exc}")
        print("   Make sure models/hand_landmarker.task exists.")
        sys.exit(1)

    # Initialize video capture
    use_pipeline = False
    pipeline = None

    if args.use_pipeline:
        try:
            from src.vision.camera import CameraPipeline

            pipeline = CameraPipeline(
                camera_index=args.camera,
                width=args.width,
                height=args.height,
                target_fps=args.fps,
            )
            pipeline.start()
            use_pipeline = True
            print("  Camera Mode    : Threaded CameraPipeline")
        except Exception as err:
            print(f"  ⚠️  CameraPipeline unavailable ({err}), falling back to cv2.VideoCapture.")

    if not use_pipeline:
        # Standalone OpenCV capture (fully modular, works without camera.py)
        cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
        if not cap.isOpened():
            # Fallback for non-Windows or direct capture
            cap = cv2.VideoCapture(args.camera)

        if not cap.isOpened():
            print(f"\n❌ Cannot open camera device {args.camera}.")
            print("   Please check your webcam connection and permissions.")
            processor.close()
            sys.exit(1)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        cap.set(cv2.CAP_PROP_FPS, args.fps)
        print("  Camera Mode    : Standalone cv2.VideoCapture (Direct)")

    window_name = f"InputProcessor Test [Cam {args.camera}] - Press Q to Quit"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    # Metrics
    total_frames = 0
    hands_detected = 0
    fps_start = time.perf_counter()
    fps_count = 0
    display_fps = 0.0
    flip_mode = not args.no_flip

    # EMA filter for paddle movement smoothing
    paddle_filter = EMAFilter(alpha=args.alpha)
    use_ema = not args.no_ema
    paddle_x: float = 0.5  # Persistent paddle coordinate across frames

    try:
        while True:
            t_frame_start = time.perf_counter()

            # Read frame
            if use_pipeline and pipeline is not None:
                frame = pipeline.read()
                if frame is None:
                    time.sleep(0.002)
                    continue
                # CameraPipeline already flipped the frame
                proc_flip = False
            else:
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.005)
                    continue
                proc_flip = flip_mode

            total_frames += 1
            fps_count += 1

            # Update rolling FPS
            elapsed = time.perf_counter() - fps_start
            if elapsed >= 1.0:
                display_fps = fps_count / elapsed
                fps_count = 0
                fps_start = time.perf_counter()

            # Process frame with InputProcessor
            inference_start = time.perf_counter()
            # If standalone, processor handles flip
            landmark = processor.process(frame, flip_horizontal=proc_flip)
            inference_ms = (time.perf_counter() - inference_start) * 1000.0

            # If standalone and flipped, also flip the display frame to match coordinates
            display_frame = frame.copy()
            if not use_pipeline and proc_flip:
                display_frame = cv2.flip(display_frame, 1)

            h, w = display_frame.shape[:2]

            # -------------------------------------------------------------
            # Visual Overlay & Hand Drawing
            # -------------------------------------------------------------
            status_text = "No Hand Detected"
            status_color = (0, 0, 255)  # Red
            handedness_str = "None"
            norm_coord_str = "N/A"
            pixel_coord_str = "N/A"
            raw_x: float | None = None

            if landmark is not None:
                hands_detected += 1
                status_text = "Hand Tracked"
                status_color = (0, 255, 0)  # Green
                handedness_str = landmark.handedness
                raw_x = landmark.x

                if use_ema:
                    paddle_x = paddle_filter.update(raw_x)
                    norm_coord_str = f"Raw:{raw_x:.3f} | EMA:{paddle_x:.3f}"
                else:
                    paddle_x = raw_x
                    norm_coord_str = f"Raw:{raw_x:.3f} (EMA off)"

                pixel_coord_str = f"({int(landmark.x * w)}, {int(landmark.y * h)}) px"

                # Draw skeleton and control point
                InputProcessor.draw_landmarks(display_frame, landmark)

            # -------------------------------------------------------------
            # Game Paddle Preview Bar (demonstrates paddle response)
            # -------------------------------------------------------------
            paddle_w = int(w * 0.18)
            paddle_h = 12
            paddle_y = h - 25

            # Paddle rail track
            cv2.rectangle(display_frame, (10, h - 30), (w - 10, h - 8), (40, 40, 40), -1)

            # Draw raw ghost outline if EMA is active to visually compare jitter
            if landmark is not None and use_ema and raw_x is not None:
                raw_clamped = max(config.CAM_X_MIN, min(config.CAM_X_MAX, raw_x))
                raw_rel = (raw_clamped - config.CAM_X_MIN) / (config.CAM_X_MAX - config.CAM_X_MIN)
                raw_center_x = int(raw_rel * (w - paddle_w)) + paddle_w // 2
                raw_left = max(10, raw_center_x - paddle_w // 2)
                raw_right = min(w - 10, raw_center_x + paddle_w // 2)
                cv2.rectangle(
                    display_frame,
                    (raw_left, paddle_y - paddle_h // 2),
                    (raw_right, paddle_y + paddle_h // 2),
                    (255, 140, 0),
                    1,
                )

            # Map smoothed paddle X to screen paddle position
            clamped_x = max(config.CAM_X_MIN, min(config.CAM_X_MAX, paddle_x))
            rel_x = (clamped_x - config.CAM_X_MIN) / (config.CAM_X_MAX - config.CAM_X_MIN)
            paddle_center_x = int(rel_x * (w - paddle_w)) + paddle_w // 2

            # Solid paddle indicator (smoothed)
            p_left = max(10, paddle_center_x - paddle_w // 2)
            p_right = min(w - 10, paddle_center_x + paddle_w // 2)
            cv2.rectangle(
                display_frame,
                (p_left, paddle_y - paddle_h // 2),
                (p_right, paddle_y + paddle_h // 2),
                (0, 255, 255),
                -1,
            )
            mode_label = (
                f"PADDLE PREVIEW (EMA a={paddle_filter.alpha:.2f})"
                if use_ema
                else "PADDLE PREVIEW (RAW)"
            )
            cv2.putText(
                display_frame,
                mode_label,
                (w // 2 - 80, h - 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (180, 180, 180),
                1,
                cv2.LINE_AA,
            )

            # -------------------------------------------------------------
            # HUD Overlay Panel
            # -------------------------------------------------------------
            hud_w, hud_h = 300, 172
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (10, 10), (10 + hud_w, 10 + hud_h), (15, 15, 15), -1)
            cv2.addWeighted(overlay, 0.65, display_frame, 0.35, 0, display_frame)
            cv2.rectangle(display_frame, (10, 10), (10 + hud_w, 10 + hud_h), (80, 80, 80), 1)

            ema_label = f"ON (a={paddle_filter.alpha:.2f})" if use_ema else "OFF"
            lines = [
                (f"FPS: {display_fps:4.1f} | Latency: {inference_ms:4.1f}ms", (0, 255, 255)),
                (f"Status: {status_text}", status_color),
                (f"Hand: {handedness_str}", (220, 220, 220)),
                (f"Coord: {norm_coord_str}", (0, 255, 180)),
                (f"Pixel: {pixel_coord_str}", (180, 180, 180)),
                (f"EMA: {ema_label} [E, +/-]", (100, 255, 255)),
                (f"Flip: {'ON (Mirror)' if proc_flip else 'OFF'} [F]", (160, 160, 255)),
            ]

            for i, (text, color) in enumerate(lines):
                cv2.putText(
                    display_frame,
                    text,
                    (20, 30 + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.48,
                    color,
                    1,
                    cv2.LINE_AA,
                )

            # Key instruction in bottom-right
            cv2.putText(
                display_frame,
                "[Q/ESC] Quit",
                (w - 95, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (200, 200, 200),
                1,
                cv2.LINE_AA,
            )

            cv2.imshow(window_name, display_frame)

            # Key controls
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):  # 'q' or ESC
                break
            elif key in (ord("f"), ord("F")):
                flip_mode = not flip_mode
                print(f"  * Horizontal flip toggled: {flip_mode}")
            elif key in (ord("e"), ord("E")):
                use_ema = not use_ema
                if use_ema:
                    paddle_filter.reset(paddle_x)
                print(f"  * EMA smoothing: {'Enabled' if use_ema else 'Disabled'}")
            elif key in (ord("+"), ord("=")):
                new_alpha = min(1.0, round(paddle_filter.alpha + 0.05, 2))
                paddle_filter.alpha = new_alpha
                print(f"  * EMA alpha increased to: {new_alpha:.2f}")
            elif key in (ord("-"), ord("_")):
                new_alpha = max(0.05, round(paddle_filter.alpha - 0.05, 2))
                paddle_filter.alpha = new_alpha
                print(f"  * EMA alpha decreased to: {new_alpha:.2f}")

    finally:
        # Cleanup
        cv2.destroyAllWindows()
        processor.close()
        if use_pipeline and pipeline is not None:
            pipeline.stop()
        elif "cap" in locals():
            cap.release()

        # Session summary
        print("\n" + "─" * 45)
        print("  Hand Tracking Test Session Summary")
        print("─" * 45)
        print(f"  Total frames      : {total_frames}")
        print(f"  Hands detected    : {hands_detected}")
        detection_pct = 100.0 * hands_detected / max(total_frames, 1)
        print(f"  Detection rate    : {detection_pct:.1f}%")
        print("─" * 45)
        if detection_pct > 30:
            print("  ✅ MediaPipe hand tracking is operational!")
        else:
            print("  ℹ️ Finished. Ensure hand is visible within camera view.")
        print()


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli_args = build_parser().parse_args()
    run_live_camera(cli_args)
