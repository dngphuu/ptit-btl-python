"""
build_windows.py
================
Automated Windows standalone build script for VisionBrick.
Packages the game into a standalone directory and creates a ready-to-distribute zip archive.
"""

from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path


def ensure_icon(root: Path) -> Path:
    icon_path = root / "assets" / "icon.ico"
    if not icon_path.exists():
        from PIL import Image

        game_element = root / "assets" / "game_element.png"
        if game_element.exists():
            img = Image.open(game_element).crop((971, 125, 971 + 65, 125 + 65))
            img.save(icon_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    return icon_path


def main() -> None:
    root = Path(__file__).resolve().parent
    dist_dir = root / "dist"
    output_dir = dist_dir / "VisionBrick"

    print("==> 1. Ensuring game icon exists...")
    icon_path = ensure_icon(root)

    print("==> 2. Running PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name",
        "VisionBrick",
        "--icon",
        str(icon_path),
        "--add-data",
        f"{root / 'assets'}{os.pathsep}assets",
        "--add-data",
        f"{root / 'models'}{os.pathsep}models",
        "--collect-all",
        "mediapipe",
        str(root / "main.py"),
    ]

    result = subprocess.run(cmd, cwd=root)
    if result.returncode != 0:
        print("PyInstaller build failed!")
        sys.exit(result.returncode)

    print("==> 3. Adding release README...")
    release_readme = output_dir / "README.txt"
    release_readme.write_text(
        "VisionBrick - Hand-Tracked Brick Breaker (v1.0.0)\n"
        "=================================================\n\n"
        "HOW TO RUN:\n"
        "  Double-click 'VisionBrick.exe'. No installation or Python required!\n\n"
        "CONTROLS:\n"
        "  - Hand Gestures: Show your hand to your webcam to control the paddle.\n"
        "  - Keyboard Fallback: Left / Right Arrow keys.\n"
        "  - Fullscreen: Press F11 or Alt + Enter.\n"
        "  - Pause: Press P or click the in-game Pause button.\n"
        "  - Settings: Adjust Audio Volume and toggle Gesture Control in Settings.\n\n"
        "Have fun breaking bricks!\n",
        encoding="utf-8",
    )

    print("==> 4. Packaging into ZIP archive...")
    zip_path = dist_dir / "VisionBrick-v1.0.0-windows-x64.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in output_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(dist_dir)
                zf.write(file, arcname)

    print(f"==> Build successful! Package created at:\n    {zip_path}")


if __name__ == "__main__":
    main()
