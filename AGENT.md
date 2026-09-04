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
│   ├── filters/
│   │   └── ema.py             # Exponential Moving Average smoother
│   └── vision/
│       ├── camera.py          # OpenCV capture, threaded frame buffer
│       └── input_processor.py # MediaPipe landmark → normalized (x, y) output
├── assets/
│   ├── sprites/ui/kenney_pixel_adventure/
│   │   ├── tiles/large/{thick,thin}_outline/   # 32×32 px PNGs  (tile_0000–0090)
│   │   ├── tiles/small/{thick,thin}_outline/   # 16×16 px PNGs  (tile_0000–0160)
│   │   └── tilesheets/{large,small}/{thick,thin}_outline/  # tilemap.png + tilemap_packed.png
│   ├── audio/                 # SFX / music
│   ├── fonts/
│   ├── shaders/
│   └── vfx/
├── tests/
├── main.py                    # thin entry point → uv run python main.py
├── pyproject.toml
└── AGENT.md
```

> **Not yet created:** `src/core/` (game loop, state machine) · `src/entities/` (paddle, ball, brick).
> Create them when implementing gameplay, following the planned architecture below.

## 3. Planned Architecture (implement as needed)

| Module                   | Responsibility                             |
| ------------------------ | ------------------------------------------ |
| `src/core/game.py`       | Main loop, clock, event dispatch           |
| `src/core/states.py`     | State machine: `Menu → Playing → GameOver` |
| `src/core/renderer.py`   | All `pygame` draw calls                    |
| `src/entities/paddle.py` | Paddle rect, move from normalized x        |
| `src/entities/ball.py`   | Ball physics, velocity                     |
| `src/entities/brick.py`  | Brick grid, HP, destruction                |

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
