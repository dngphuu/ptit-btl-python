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
# MediaPipe Hands (Tasks API – mediapipe >= 1.0)
# ---------------------------------------------------------------------------
MP_MAX_NUM_HANDS: int = 1
MP_MODEL_COMPLEXITY: int = 0  # 0 = lite (fastest)
MP_MIN_DETECTION_CONFIDENCE: float = 0.6
MP_MIN_TRACKING_CONFIDENCE: float = 0.5
# Minimum confidence that a hand is present in a frame (Tasks API only)
MP_MIN_PRESENCE_CONFIDENCE: float = 0.5

# Path to the hand_landmarker.task bundle (relative to repo root).
# Download via: https://storage.googleapis.com/mediapipe-models/hand_landmarker/
#               hand_landmarker/float16/latest/hand_landmarker.task
MP_MODEL_PATH: str = "models/hand_landmarker.task"

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

# ---------------------------------------------------------------------------
# Audio / BGM / SFX
# ---------------------------------------------------------------------------
MENU_BGM_PATH: str = "assets/audio/main-menu-bgm.mp3"
MENU_BGM_VOLUME: float = 0.5
GAME_BGM_PATH: str = "assets/audio/main-game-bgm.mp3"
GAME_BGM_VOLUME: float = 0.5
SFX_CLICK_PATH: str = "assets/audio/sfx_click.ogg"
SFX_PADDLE_HIT_PATH: str = "assets/audio/sfx_paddle_hit.ogg"
SFX_BRICK_HIT_PATH: str = "assets/audio/sfx_brick_hit.ogg"
SFX_BRICK_DESTROY_PATH: str = "assets/audio/sfx_brick_destroy.ogg"
SFX_LEVEL_COMPLETE_PATH: str = "assets/audio/sfx_level_complete.ogg"
SFX_LEVEL_FAIL_PATH: str = "assets/audio/sfx_level_fail.ogg"

# ---------------------------------------------------------------------------
# Main menu / UI assets
# ---------------------------------------------------------------------------
MAIN_MENU_BG_PATH: str = "assets/backgrounds/main_menu_frame.png"
MAIN_TITLE_PATH: str = "assets/sprites/ui/menu/main_title.png"
MAIN_MENU_BTN_PATH: str = "assets/sprites/ui/menu/main_menu_btn_bg.png"
FONT_PRIMARY_PATH: str = "assets/fonts/ThaleahFat.ttf"
FONT_SECONDARY_PATH: str = "assets/fonts/Minecraft.ttf"

# ---------------------------------------------------------------------------
# Gameplay / UI assets
# ---------------------------------------------------------------------------
MAIN_GAME_BG_PATH: str = "assets/backgrounds/main_game_frame.png"
GAME_EXIT_BTN_PATH: str = "assets/sprites/ui/game/btn_exit.png"
GAME_PAUSE_BTN_PATH: str = "assets/sprites/ui/game/btn_pause.png"
HEART_ICON_PATH: str = "assets/sprites/ui/game/heart.png"
HEART_SHEET_PATH: str = "assets/heart.png"
GAME_EXIT_BTN_RECT: tuple[int, int, int, int] = (684, 20, 99, 99)
GAME_PAUSE_BTN_RECT: tuple[int, int, int, int] = (20, 20, 99, 99)
GAME_HUD_RECT: tuple[int, int, int, int] = (144, 46, 516, 136)

# ---------------------------------------------------------------------------
# Playfield container rectangle (inside the hieroglyph stone frame)
# ---------------------------------------------------------------------------
PLAYFIELD_X: int = 176
PLAYFIELD_Y: int = 236
PLAYFIELD_WIDTH: int = 448
PLAYFIELD_HEIGHT: int = 340
PLAYFIELD_RECT: tuple[int, int, int, int] = (
    PLAYFIELD_X,
    PLAYFIELD_Y,
    PLAYFIELD_WIDTH,
    PLAYFIELD_HEIGHT,
)

# ---------------------------------------------------------------------------
# Brick assets (assets/sprites/tiles/bricks_export/ – edited transparent PNGs)
# ---------------------------------------------------------------------------
BRICKS_ASSET_DIR: str = "assets/sprites/tiles/bricks_export"

# 6 active brick colours (grey was corrupted and removed)
BRICK_COLORS: tuple[str, ...] = (
    "red",  # 0
    "orange",  # 1
    "yellow",  # 2
    "green",  # 3
    "blue",  # 4
    "purple",  # 5
)

# ---------------------------------------------------------------------------
# Brick grid layout (precisely fitted inside the upper portion of playfield)
# ---------------------------------------------------------------------------
BRICK_GRID_COLS: int = 10  # 10 columns across the stone pool
BRICK_GRID_ROWS: int = 9  # 9 rows matching the game mockup
BRICK_HORIZONTAL_GAP: int = 2  # horizontal gap between bricks (px)
BRICK_VERTICAL_GAP: int = 2  # vertical gap between bricks (px)
BRICK_MARGIN_X: int = 14  # horizontal margin between playfield edge and bricks
BRICK_MARGIN_TOP: int = 2  # top margin below the top stone beam
BRICK_HEIGHT: int = 16  # nominal brick height (px)
BRICK_MAX_HEIGHT_RATIO: float = 0.55  # brick wall occupies upper portion of playfield

# Compatibility aliases
BRICK_GAP_X: int = BRICK_HORIZONTAL_GAP
BRICK_GAP_Y: int = BRICK_VERTICAL_GAP
BRICK_H: int = BRICK_HEIGHT
BRICK_W: int = 40
BRICK_GRID_ORIGIN_X: int = PLAYFIELD_X + 15  # 191
BRICK_GRID_ORIGIN_Y: int = PLAYFIELD_Y + BRICK_MARGIN_TOP  # 238
