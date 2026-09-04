# Agent Guidelines: Hand-Tracked Brick Breaker

## 1. Project Overview
- **Goal:** 2D Brick Breaker game controlled via real-time webcam hand gestures (MediaPipe) with fallback to keyboard/mouse.
- **Tech Stack:** Python 3.10+, `uv`, `pygame`, `opencv-python`, `mediapipe`, `numpy`.
- **Target Performance:** 60 FPS game loop, 30 FPS camera feed; must run smoothly on standard multi-core CPUs without dedicated GPU acceleration.

## 2. Architecture & Directory Layout
- `src/core/`: Game loop, state manager (Menu, Playing, GameOver), display/renderer.
- `src/entities/`: Game actors (`paddle.py`, `ball.py`, `brick.py`).
- `src/vision/`: Camera capture and MediaPipe landmark extraction (`gesture_controller.py`).
- `src/filters/`: Coordinate smoothing algorithms (EMA, Linear Interpolation `lerp`).
- `src/config.py`: Global constants (screen dimensions, ball speed, smoothing coefficients, thresholds).
- `tests/`: Unit tests for collision math, physics edge cases, and filter stability.

## 3. Essential Commands
- **Install dependencies:** `uv sync`
- **Run application:** `uv run python -m src.main`
- **Run debug mode (camera overlay + FPS counter):** `uv run python -m src.main --debug`
- **Run tests:** `uv run pytest tests/`
- **Lint & Format:** `uv run ruff check . --fix && uv run ruff format .`

## 4. Code Style & Conventions
- **Strict Typing:** Always annotate function signatures and variables using `typing`, `pygame.Rect`, and `numpy.ndarray`.
- **Decoupled Architecture:** `src/vision/` must only output normalized coordinates ($X \in [0.0, 1.0]$). It must never modify game entity state or `paddle.rect` directly.
- **No Magic Numbers:** Move all physics parameters, dimensions, and gesture tolerances into `src/config.py`.
- **Naming:** `snake_case` for files, functions, and variables; `PascalCase` for classes; `UPPER_CASE` for constants.

## 5. Non-Negotiable Constraints
1. **Non-Blocking Game Loop:** Never invoke blocking frame capture or inference inside the Pygame render thread. Handle camera polling in a dedicated worker thread or async buffer.
2. **Offline Testability:** Core gameplay, physics, and collisions must be testable via keyboard/mouse or mock coordinates without an active webcam.
3. **Preserve Smoothing Logic:** Do not replace the existing EMA/Lerp pipeline with heavy filters. Tune coefficients via `config.py` instead.
4. **Scope Isolation:** Changes to collision/physics must not touch `src/vision/`, and vision adjustments must not touch entity rendering.
5. **No Heavy External Models:** Rely solely on MediaPipe Hands; do not introduce heavy deep learning frameworks (e.g., PyTorch, TensorFlow, ONNX).

## 6. Execution Workflow
1. **Analyze:** Inspect affected files and verify constants in `src/config.py`.
2. **Plan:** State minimal planned modifications in 2-3 bullet points before writing code.
3. **Implement:** Keep diffs localized and atomic.
4. **Validate:** Run `uv run pytest` and `uv run ruff check .` to verify zero regression before closing the task.