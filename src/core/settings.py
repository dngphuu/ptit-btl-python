"""
src/core/settings.py
====================
Persistent game settings (audio volumes, control mode).
"""

from __future__ import annotations

import json
import os

_SETTINGS_FILE = "settings.json"


class GameSettings:
    """Global mutable settings, persisted to disk as JSON."""

    music_volume: float = 0.5   # 0.0 – 1.0
    sfx_volume: float = 1.0     # 0.0 – 1.0
    control_mode: str = "gesture"  # "keyboard" | "gesture"

    # Convenience read-only helpers
    @classmethod
    def is_music_on(cls) -> bool:
        return cls.music_volume > 0.0

    @classmethod
    def is_sfx_on(cls) -> bool:
        return cls.sfx_volume > 0.0

    @classmethod
    def is_gesture_on(cls) -> bool:
        return cls.control_mode == "gesture"

    @classmethod
    def set_gesture_control(cls, enabled: bool) -> None:
        cls.control_mode = "gesture" if enabled else "keyboard"
        cls.save()

    @classmethod
    def get_volume(cls) -> float:
        return cls.music_volume

    @classmethod
    def set_volume(cls, val: float) -> None:
        clamped = max(0.0, min(1.0, round(float(val), 2)))
        cls.music_volume = clamped
        cls.sfx_volume = clamped
        cls.save()

    @classmethod
    def set_music_volume(cls, val: float) -> None:
        cls.music_volume = max(0.0, min(1.0, round(float(val), 2)))
        cls.save()

    @classmethod
    def set_sfx_volume(cls, val: float) -> None:
        cls.sfx_volume = max(0.0, min(1.0, round(float(val), 2)))
        cls.save()

    # ── persistence ───────────────────────────────────────────────────────

    @classmethod
    def load(cls) -> None:
        try:
            if os.path.exists(_SETTINGS_FILE):
                with open(_SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                cls.music_volume = float(data.get("music_volume", 0.5))
                cls.sfx_volume = float(data.get("sfx_volume", 1.0))
                cls.control_mode = data.get("control_mode", "gesture")
        except Exception:
            pass

    @classmethod
    def save(cls) -> None:
        try:
            with open(_SETTINGS_FILE, "w") as f:
                json.dump(
                    {
                        "music_volume": round(cls.music_volume, 2),
                        "sfx_volume": round(cls.sfx_volume, 2),
                        "control_mode": cls.control_mode,
                    },
                    f,
                )
        except Exception:
            pass


# Load at import time so every module sees the saved values immediately.
GameSettings.load()
