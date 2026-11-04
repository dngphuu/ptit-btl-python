# 🧱 VisionBrick – Hand-Tracked Brick Breaker

[![Release](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/dngphuu/ptit-btl-python/releases)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Pygame-CE](https://img.shields.io/badge/pygame--ce-2.5+-informational.svg)](https://pyga.me)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Tasks%20Vision-FF6F00.svg)](https://developers.google.com/mediapipe)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

> **VisionBrick** is a modern 2D Brick Breaker arcade game built with **Python**, **pygame-ce**, and **MediaPipe**. Play using real-time webcam hand gestures or traditional keyboard controls, all framed within a rich retro cave and hieroglyph stone aesthetic.

---

## 🎮 Game Screenshots

| Main Menu | Gameplay & Vision Feed | Settings Menu |
| :---: | :---: | :---: |
| ![Main Menu](mockups/main_menu.png) | ![Main Gameplay](mockups/main_game.png) | ![Settings Menu](mockups/settings_menu.png) |

---

## ✨ Features

- 🖐️ **Webcam Gesture Control**: Real-time hand landmark tracking powered by **MediaPipe Tasks API (HandLandmarker)**. Steer your paddle effortlessly by moving your hand horizontally in front of the camera.
- 📉 **Jitter-Free Filtering**: Features Exponential Moving Average (EMA) smoothing to translate camera input into fluid, natural paddle movement.
- ⌨️ **Keyboard Fallback**: Smooth transition between gesture control and Left/Right Arrow keys anytime.
- 🎨 **Retro Pixel-Art Graphics**: Custom cave hieroglyph stone borders, glowing torches, animated ball, and multi-colored bricks with dynamic debris particle effects.
- 🎵 **Dynamic BGM & SFX**: Retro background music and crunchy 8-bit sound effects for paddle bounces, brick destruction, victories, and losses.
- ⚙️ **Interactive Settings Menu**: Fully custom stone-themed UI with sliders for volume management and an on/off toggle for gesture tracking.
- 🏆 **High Score & Setting Persistence**: Automatically stores and recalls your highest scores and preferences across sessions.
- 🖥️ **Scalable Display**: Logical 800×600 aspect ratio automatically preserved across window resizing and fullscreen mode (`F11` or `Alt+Enter`).
- 🚀 **CPU-Optimized**: Multi-threaded camera pipeline keeps the 60 FPS render loop responsive without blocking on vision inference.

---

## 📦 Download Pre-built Binary (Windows)

No Python installation required! Download the ready-to-play Windows standalone package directly:

1. Go to [**Releases**](https://github.com/dngphuu/ptit-btl-python/releases) and download `VisionBrick-v1.0.0-windows-x64.zip`.
2. Extract the ZIP file to any folder on your computer.
3. Double-click **`VisionBrick.exe`** to launch and play immediately!

---

## 🕹️ Controls

| Action | Gesture / Mouse | Keyboard |
| :--- | :--- | :--- |
| **Move Paddle** | Move hand left / right in front of webcam | <kbd>←</kbd> / <kbd>→</kbd> or <kbd>A</kbd> / <kbd>D</kbd> |
| **Pause Game** | Click **[PAUSE]** button | <kbd>P</kbd> |
| **Toggle Fullscreen** | — | <kbd>F11</kbd> or <kbd>Alt</kbd> + <kbd>Enter</kbd> |
| **Quit Game** | Click **[EXIT]** button | <kbd>Esc</kbd> / Close Window |

---

## 🛠️ Local Development & Setup

### Prerequisites
- Python 3.10 or higher
- A working webcam (for gesture tracking mode)
- Recommended: [`uv`](https://docs.astral.sh/uv/) for blazing-fast package management

### 1. Clone the repository
```bash
git clone https://github.com/dngphuu/ptit-btl-python.git
cd ptit-btl-python
```

### 2. Install dependencies
Using `uv`:
```bash
uv sync
```
Or using standard `pip`:
```bash
pip install -e .
pip install -e ".[dev]"
```

### 3. Run the game
```bash
uv run python main.py
```

### 4. Run tests and linting
```bash
# Run unit tests
uv run pytest

# Check code formatting & lint
uv run ruff check .
```

---

## 🔨 Building the Windows Executable

You can build the standalone `.exe` and `.zip` distribution at any time using the bundled automated build script:

```bash
uv run python build_windows.py
```

The output standalone folder and zip archive will be generated in `dist/`:
- `dist/VisionBrick/VisionBrick.exe`
- `dist/VisionBrick-v1.0.0-windows-x64.zip`

---

## 📂 Project Structure

```
ptit-btl-python/
├── .github/workflows/         # CI/CD workflows (automatic release build)
├── assets/                    # Audio, fonts, backgrounds, and sprite sheets
│   ├── audio/                 # BGM and SFX (.mp3, .ogg)
│   ├── backgrounds/           # Frame textures
│   ├── fonts/                 # TTF pixel fonts
│   └── sprites/               # UI buttons, tiles, bricks
├── mockups/                   # Design previews and mockups
├── models/                    # MediaPipe hand_landmarker.task model
├── src/
│   ├── config.py              # Centralized configuration & resource resolver
│   ├── core/                  # Audio manager, game states, settings persistence
│   ├── entities/              # Ball, Paddle, BrickGrid, Debris particles, Playfield
│   ├── filters/               # Exponential Moving Average (EMA) smoother
│   ├── screens/               # MainMenu, GameplayScreen, SettingsMenu
│   ├── ui/                    # UI button and interactive widgets
│   └── vision/                # OpenCV camera pipeline & MediaPipe input processor
├── tests/                     # Pytest unit tests
├── build_windows.py           # Automated PyInstaller build script
├── main.py                    # Main game entry point & loop
├── pyproject.toml             # Project metadata & dependencies
└── README.md
```

---

## 📜 License

This project is open-source and developed as a university coursework project (PTIT).
Distributed under the [MIT License](LICENSE).
