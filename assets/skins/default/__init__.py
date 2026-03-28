# assets/skins/default/__init__.py
# Default orange cat skin for Claude Desktop Pet.

import os
import sys

# Add src to path to import skin_registry utility
_src_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from skin_registry import load_module_from_path

# Load frames.py using shared utility
_frames_path = os.path.join(os.path.dirname(__file__), "frames.py")
_frames_module = load_module_from_path("default_frames", _frames_path)

FRAMES = _frames_module.FRAMES
FRAME_INTERVALS = _frames_module.FRAME_INTERVALS
STATE_MOTION = _frames_module.STATE_MOTION

META = {
    "name": "小橘猫",
    "id": "default",
}

ROWS = 6
COLS = 8

__all__ = ["META", "ROWS", "COLS", "FRAMES", "FRAME_INTERVALS", "STATE_MOTION"]
