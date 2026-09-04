# Agent Guidelines: Hand-Tracked Brick Breaker (VisionBrick)

## 1. Project Snapshot

- **Goal:** 2D Brick Breaker controlled via webcam hand gestures (MediaPipe); keyboard/mouse fallback.
- **Stack:** Python 3.10+, `uv`, `pygame-ce`, `opencv-python`, `mediapipe`, `numpy`.
- **Performance target:** 60 FPS game loop · 30 FPS camera feed · CPU-only.

## 2. Actual Directory Layout

```
ptit-btl-python/
├── src/
│   ├── config.py              # ALL constants live here (dimensions, speeds, thresholds)
│   ├── core/
│   │   └── states.py          # GameState enum (MAIN_MENU, PLAYING, SETTINGS, GAME_OVER, QUIT)
│   ├── filters/
│   │   └── ema.py             # Exponential Moving Average smoother
│   ├── screens/
│   │   └── main_menu.py       # Main menu screen (title banner, buttons, animated background)
│   ├── ui/
│   │   ├── button.py          # MenuButton component
│   │   ├── gif_background.py  # Animated GIF background loader & renderer
│   │   └── nine_slice.py      # 9-slice panel rendering
│   └── vision/
│       ├── camera.py          # OpenCV capture, threaded frame buffer
│       └── input_processor.py # MediaPipe landmark → normalized (x, y) output
├── assets/
│   ├── audio/                 # SFX / music
│   ├── backgrounds/           # Background graphics (e.g. animated GIF)
│   ├── fonts/                 # TTF fonts (Minecraft.ttf, ThaleahFat.ttf)
│   ├── shaders/
│   ├── sprites/
│   │   ├── tilemaps/          # Block, pattern, platformer tilemaps
│   │   ├── tiles/             # Individual tile sprites
│   │   └── ui/
│   │       ├── kenney_pixel_adventure/  # UI tiles (large/small, thick/thin outline)
│   │       └── menu/                    # Menu UI textures (main_menu_btn_bg, main_title_bg)
│   └── vfx/
├── tests/
│   ├── test_filters.py
│   └── test_input_processor.py
├── main.py                    # Entry point & state machine loop → uv run python main.py
├── pyproject.toml
└── AGENT.md
```

> **Current status:**
> - **Implemented:** Hand tracking vision pipeline (`src/vision/`), EMA filter (`src/filters/`), Main menu screen & UI primitives (`src/screens/`, `src/ui/`), GameState machine (`src/core/states.py`, `main.py`).
> - **Next up:** Gameplay screen / game loop (`src/core/game.py` or `src/screens/gameplay.py`), core entities (`src/entities/paddle.py`, `ball.py`, `brick.py`).

## 3. Architecture & Roadmap

| Module                   | Responsibility                             | Status      |
| ------------------------ | ------------------------------------------ | ----------- |
| `src/vision/camera.py`   | OpenCV capture, threaded frame buffer      | Implemented |
| `src/vision/input_processor.py` | MediaPipe landmark → normalized (x, y) | Implemented |
| `src/filters/ema.py`     | Coordinate smoothing filter                | Implemented |
| `src/core/states.py`     | GameState enum (`MAIN_MENU`, `PLAYING`...) | Implemented |
| `src/ui/`                | UI primitives (`button`, `nine_slice`, etc.)| Implemented |
| `src/screens/main_menu.py`| Main menu screen & event handling         | Implemented |
| `src/entities/paddle.py` | Paddle rect, move from normalized x        | Planned     |
| `src/entities/ball.py`   | Ball physics, velocity, collisions         | Planned     |
| `src/entities/brick.py`  | Brick grid, HP, destruction                | Planned     |
| `src/core/game.py`       | Gameplay session loop & collision manager  | Planned     |

## 4. Essential Commands

```bash
uv sync                              # install deps
uv run python main.py                # run game
uv run python main.py --debug        # camera overlay + FPS counter
uv run pytest tests/                 # run tests
uv run ruff check . --fix && uv run ruff format .   # lint + format
```

## 5. Code Conventions

- **Types:** Annotate all signatures; use `pygame.Rect`, `numpy.ndarray`, `tuple[float, float]`.
- **Constants:** Every magic number → `src/config.py`. Never hardcode in entity/vision files.
- **Naming:** `snake_case` files/vars/funcs · `PascalCase` classes · `UPPER_CASE` constants.
- **Vision boundary:** `src/vision/` outputs **only** normalized coords `(x ∈ [0,1], y ∈ [0,1])`. It never touches entity state.

## 6. Hard Constraints

1. **Non-blocking loop:** Camera capture runs in a worker thread. Never call blocking I/O in the Pygame render thread.
2. **Offline testable:** Physics/collision tests must run with mock coords — no webcam required.
3. **Keep EMA/Lerp:** Tune smoothing via `config.py`; do not swap in heavier filters.
4. **Scope isolation:** Physics changes → no edits to `src/vision/`; vision changes → no edits to entity rendering.
5. **No heavy ML:** MediaPipe Hands only. No PyTorch / TensorFlow / ONNX.

## 7. Workflow

1. **Locate:** Check `src/config.py` for relevant constants before touching any entity/vision file.
2. **Plan:** Write 2-3 bullet points of intent before generating code.
3. **Implement:** Atomic, localized diffs only.
4. **Validate:** `uv run pytest` + `uv run ruff check .` must pass before closing.
