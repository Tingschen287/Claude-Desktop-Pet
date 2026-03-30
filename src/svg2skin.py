# src/svg2skin.py
# SVG to skin converter for Claude Desktop Pet.

from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtCore import Qt
from pathlib import Path
from typing import Optional
import json


def svg_to_pixel_grid(svg_path: str, rows: int, cols: int) -> list:
    """Convert an SVG file to a pixel grid.

    Args:
        svg_path: Path to the SVG file
        rows: Number of rows in the output grid
        cols: Number of columns in the output grid

    Returns:
        2D list of color strings ("#RRGGBB" or "transparent")
    """
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        raise ValueError(f"Invalid SVG file: {svg_path}")

    # Render to a small image
    image = QImage(cols, rows, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    # Extract pixel colors
    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            color = image.pixelColor(x, y)
            if color.alpha() < 128:
                row.append("transparent")
            else:
                row.append(color.name())  # "#RRGGBB"
        grid.append(row)

    return grid


def generate_all_states(base_frame: list, config: dict) -> dict:
    """Generate all 7 state frames from a base frame.

    Args:
        base_frame: The base pixel grid (2D list)
        config: Configuration dict with eye positions, body color, etc.

    Returns:
        dict mapping state names to lists of frames
    """
    rows = len(base_frame)
    cols = len(base_frame[0]) if rows > 0 else 0

    eye_left = config.get("eye_left", [2, 2])
    eye_right = config.get("eye_right", [2, 5])
    body_color = config.get("body_color", "#FF6432")
    progress_row = config.get("progress_row", 4)

    # Dim colors for unconfigured state
    dim_body = _dim_color(body_color, 0.4)
    dim_eye = _dim_color(body_color, 0.5)

    # Animation colors
    purple = "#AA44FF"
    yellow = "#FFDD44"
    green = "#44FF88"
    red = "#FF3344"

    frames = {}

    # unconfigured: single dim frame
    frames["unconfigured"] = [_apply_color(base_frame, body_color, dim_body, {tuple(eye_left), tuple(eye_right)}, dim_eye)]

    # idle: 4 frames with blink
    frames["idle"] = [
        _copy_frame(base_frame),
        _copy_frame(base_frame),
        _set_pixels(_copy_frame(base_frame), [eye_left, eye_right], body_color),
        _copy_frame(base_frame),
    ]

    # thinking: eyes move left-center-right with purple
    frames["thinking"] = [
        _set_pixels(_copy_frame(base_frame), eye_positions(eye_left, eye_right, 0), purple),
        _set_pixels(_copy_frame(base_frame), eye_positions(eye_left, eye_right, -1), purple),
        _set_pixels(_copy_frame(base_frame), eye_positions(eye_left, eye_right, 0), purple),
        _set_pixels(_copy_frame(base_frame), eye_positions(eye_left, eye_right, 1), purple),
    ]

    # reading: eyes scan with yellow
    frames["reading"] = [
        _set_pixels(_copy_frame(base_frame), eye_positions(eye_left, eye_right, 0), yellow),
        _set_pixels(_copy_frame(base_frame), eye_positions(eye_left, eye_right, -1), yellow),
        _set_pixels(_copy_frame(base_frame), eye_positions(eye_left, eye_right, 0), yellow),
        _set_pixels(_copy_frame(base_frame), eye_positions(eye_left, eye_right, 1), yellow),
    ]

    # writing: progress bar sweeps
    frames["writing"] = [
        _add_progress_bar(_copy_frame(base_frame), progress_row, 0, green),
        _add_progress_bar(_copy_frame(base_frame), progress_row, cols // 4, green),
        _add_progress_bar(_copy_frame(base_frame), progress_row, cols // 2, green),
        _add_progress_bar(_copy_frame(base_frame), progress_row, cols * 3 // 4, green),
    ]

    # executing: wide eyes shake
    frames["executing"] = [
        _set_pixels(_copy_frame(base_frame), wide_eye_positions(eye_left, eye_right, 0), yellow),
        _set_pixels(_copy_frame(base_frame), wide_eye_positions(eye_left, eye_right, 1), yellow),
        _set_pixels(_copy_frame(base_frame), wide_eye_positions(eye_left, eye_right, 0), yellow),
        _set_pixels(_copy_frame(base_frame), wide_eye_positions(eye_left, eye_right, 1), yellow),
    ]

    # waiting: red eyes flash
    frames["waiting"] = [
        _set_pixels(_copy_frame(base_frame), [eye_left, eye_right], red),
        _set_pixels(_copy_frame(base_frame), [eye_left, eye_right], body_color),
    ]

    return frames


def _copy_frame(frame: list) -> list:
    """Deep copy a frame."""
    return [row[:] for row in frame]


def _set_pixels(frame: list, positions: list, color: str) -> list:
    """Set multiple pixels to a color."""
    for pos in positions:
        r, c = pos[0], pos[1]
        if 0 <= r < len(frame) and 0 <= c < len(frame[0]):
            frame[r][c] = color
    return frame


def _apply_color(frame: list, old_color: str, new_color: str, exceptions: set, exception_color: str) -> list:
    """Replace colors, with exceptions getting a different color."""
    result = []
    for r, row in enumerate(frame):
        new_row = []
        for c, pixel in enumerate(row):
            if (r, c) in exceptions:
                new_row.append(exception_color)
            elif pixel == old_color:
                new_row.append(new_color)
            else:
                new_row.append(pixel)
        result.append(new_row)
    return result


def _dim_color(hex_color: str, factor: float) -> str:
    """Dim a color by a factor."""
    if hex_color.startswith("#") and len(hex_color) == 7:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
    return hex_color


def _add_progress_bar(frame: list, row: int, cols: int, color: str) -> list:
    """Add a progress bar to a frame."""
    if 0 <= row < len(frame):
        for c in range(1, min(cols + 1, len(frame[0]) - 1)):
            frame[row][c] = color
    return frame


def eye_positions(left: list, right: list, offset: int) -> list:
    """Get eye positions with horizontal offset."""
    return [
        [left[0], max(0, left[1] + offset)],
        [right[0], min(7, right[1] + offset)]
    ]


def wide_eye_positions(left: list, right: list, offset: int) -> list:
    """Get wide eye positions (2 pixels per eye)."""
    return [
        [left[0], max(0, left[1] - 1 + offset)],
        [left[0], left[1] + offset],
        [right[0], right[1] + offset],
        [right[0], min(7, right[1] + 1 + offset)]
    ]


# Default frame intervals and motion (same as built-in skins)
DEFAULT_FRAME_INTERVALS = {
    "unconfigured": 1000,
    "idle": 600,
    "thinking": 150,
    "reading": 300,
    "writing": 200,
    "executing": 80,
    "waiting": 400,
}

DEFAULT_STATE_MOTION = {
    "unconfigured": "none",
    "idle": "float",
    "thinking": "tremble",
    "reading": "none",
    "writing": "none",
    "executing": "shake",
    "waiting": "none",
}


def load_config(config_path: Path) -> dict:
    """Load skin configuration from JSON file."""
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def create_skin_from_svg(svg_path: str, config: dict, output_dir: Path) -> bool:
    """Create a complete skin module from an SVG file.

    Args:
        svg_path: Path to the SVG file
        config: Skin configuration (name, eye positions, etc.)
        output_dir: Directory to create the skin module in

    Returns:
        True if successful, False otherwise
    """
    try:
        skin_name = config.get("name", Path(svg_path).stem)
        skin_id = config.get("id", skin_name.lower().replace(" ", "_"))
        rows = config.get("rows", 6)
        cols = config.get("cols", 8)

        # Convert SVG to base frame
        base_frame = svg_to_pixel_grid(svg_path, rows, cols)

        # Generate all state frames
        frames = generate_all_states(base_frame, config)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate frames.py
        frames_content = _generate_frames_py(skin_id, frames, rows, cols)
        (output_dir / "frames.py").write_text(frames_content, encoding="utf-8")

        # Generate __init__.py
        init_content = _generate_init_py(skin_name, skin_id, rows, cols)
        (output_dir / "__init__.py").write_text(init_content, encoding="utf-8")

        return True
    except Exception as e:
        print(f"Error creating skin: {e}")
        return False


def _generate_frames_py(skin_id: str, frames: dict, rows: int, cols: int) -> str:
    """Generate frames.py content."""
    lines = [
        f"# Auto-generated skin frames for {skin_id}",
        f"# Grid: {rows} rows x {cols} columns",
        "",
        "FRAMES = {",
    ]

    for state, state_frames in frames.items():
        lines.append(f'    "{state}": [')
        for frame in state_frames:
            lines.append(f"        {frame},")
        lines.append("    ],")

    lines.extend([
        "}",
        "",
        "FRAME_INTERVALS = {",
    ])

    for state, interval in DEFAULT_FRAME_INTERVALS.items():
        lines.append(f'    "{state}": {interval},')

    lines.extend([
        "}",
        "",
        "STATE_MOTION = {",
    ])

    for state, motion in DEFAULT_STATE_MOTION.items():
        lines.append(f'    "{state}": "{motion}",')

    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def _generate_init_py(name: str, skin_id: str, rows: int, cols: str) -> str:
    """Generate __init__.py content."""
    return f'''# Auto-generated skin module
from .frames import FRAMES, FRAME_INTERVALS, STATE_MOTION

META = {{
    "name": "{name}",
    "id": "{skin_id}",
}}

ROWS = {rows}
COLS = {cols}

__all__ = ["META", "ROWS", "COLS", "FRAMES", "FRAME_INTERVALS", "STATE_MOTION"]
'''
