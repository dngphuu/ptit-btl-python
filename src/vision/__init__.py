"""src/vision - computer-vision subsystem for VisionBrick."""

from __future__ import annotations

# Make CameraPipeline import graceful so vision works standalone on separate branches
try:
    from src.vision.camera import CameraPipeline
except ImportError:  # pragma: no cover
    CameraPipeline = None  # type: ignore[assignment, misc]

from src.vision.input_processor import HAND_CONNECTIONS, HandLandmark, InputProcessor

__all__ = ["CameraPipeline", "HAND_CONNECTIONS", "HandLandmark", "InputProcessor"]
