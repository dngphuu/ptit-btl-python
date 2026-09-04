"""
src/config.py
=============
Global constants for VisionBrick.  All tunable parameters live here so that
no magic numbers appear elsewhere in the codebase.
"""

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
TARGET_FPS: int = 60  # Pygame render loop target

# ---------------------------------------------------------------------------
# Camera / Vision pipeline
# ---------------------------------------------------------------------------
CAMERA_INDEX: int = 0  # Default webcam device index
CAMERA_WIDTH: int = 640
CAMERA_HEIGHT: int = 480
CAMERA_TARGET_FPS: int = 30  # Desired capture frame rate

# How long (seconds) the pipeline waits when the queue is full before
# dropping the frame and moving on.  Keeps the worker non-blocking.
CAMERA_QUEUE_TIMEOUT: float = 0.005  # 5 ms

# Maximum frames held in the shared buffer.  1 = latest-frame-only (minimal
# latency); higher values give the consumer more headroom but add lag.
CAMERA_QUEUE_MAXSIZE: int = 1

# ---------------------------------------------------------------------------
# MediaPipe Hands
# ---------------------------------------------------------------------------
MP_MAX_NUM_HANDS: int = 1
MP_MODEL_COMPLEXITY: int = 0  # 0 = lite (fastest)
MP_MIN_DETECTION_CONFIDENCE: float = 0.6
MP_MIN_TRACKING_CONFIDENCE: float = 0.5

# The landmark index used for paddle control (index-finger MCP = 5).
HAND_LANDMARK_INDEX: int = 5

# ---------------------------------------------------------------------------
# Coordinate mapping  (camera X → screen X)
# ---------------------------------------------------------------------------
# Normalised camera X range that maps to [0, SCREEN_WIDTH].
# Values outside this window are clamped.
CAM_X_MIN: float = 0.15
CAM_X_MAX: float = 0.85

# ---------------------------------------------------------------------------
# EMA smoothing
# ---------------------------------------------------------------------------
EMA_ALPHA: float = 0.30  # Higher = more responsive, more jitter

# ---------------------------------------------------------------------------
# Paddle
# ---------------------------------------------------------------------------
PADDLE_WIDTH: int = 100
PADDLE_HEIGHT: int = 14
PADDLE_SPEED: int = 8  # pixels / frame (keyboard fallback)
PADDLE_Y_OFFSET: int = 40  # distance from bottom of screen
