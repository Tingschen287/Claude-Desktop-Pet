# assets/skins/crab/frames.py
# Crab skin frame data for Claude Desktop Pet.
# Grid: 6 rows x 10 columns. Colors are "#RRGGBB" or "transparent".

T = "transparent"  # Transparent
O = "#FF6432"  # Orange (body) - same as default cat skin
B = "#000000"  # Black (eyes)
G = "#44FF88"  # Green (writing progress bar)
R = "#FF3344"  # Red (waiting eye flash)
D = "#442211"  # Dim orange (unconfigured body) - same as default cat skin
DE = "#553322"  # Dim eye (unconfigured) - same as default cat skin


def _make_crab_body(body=O, eye_color=B, left_eye_col=3, right_eye_col=6, bar_cols=0):
    """Build one 6x10 crab frame."""
    # Row 0: Body top (8 columns, centered)
    row0 = [T, body, body, body, body, body, body, body, body, T]

    # Row 1: Claws at edges + eyes
    row1 = [body, body, body, body, body, body, body, body, body, body]
    row1[left_eye_col] = eye_color
    row1[right_eye_col] = eye_color

    # Row 2: Body with progress bar
    row2 = [T, body, body, body, body, body, body, body, body, T]
    if bar_cols > 0:
        for i in range(bar_cols):
            if i < 6:
                row2[2 + i] = G

    # Row 3: Body bottom
    row3 = [T, body, body, body, body, body, body, body, body, T]

    # Row 4: Legs (single row)
    row4 = [T, T, body, body, T, T, body, body, T, T]

    # Row 5: Empty bottom
    row5 = [T] * 10

    return [row0, row1, row2, row3, row4, row5]


def _make_claw_frame(body=O, eye_color=B, left_claw_open=True, right_claw_open=True, left_eye_col=3, right_eye_col=6):
    """Build crab frame with animated claws."""
    frame = _make_crab_body(body, eye_color, left_eye_col, right_eye_col)

    # Claws at edges of row 1
    if not left_claw_open:
        frame[1][0] = T
    if not right_claw_open:
        frame[1][9] = T

    return frame


FRAMES = {
    # Static dim appearance - no animation
    "unconfigured": [
        _make_crab_body(body=D, eye_color=DE),
    ],

    # Black eyes, slow blink cycle (4 frames)
    "idle": [
        _make_crab_body(),           # f0: eyes open
        _make_crab_body(),           # f1: eyes open (hold)
        _make_crab_body(eye_color=O), # f2: blink closed
        _make_crab_body(),           # f3: eyes reopen
    ],

    # Eyes shifting left-center-right (4 frames)
    "thinking": [
        _make_crab_body(left_eye_col=3, right_eye_col=6),  # f0: center
        _make_crab_body(left_eye_col=2, right_eye_col=5),  # f1: look left
        _make_crab_body(left_eye_col=3, right_eye_col=6),  # f2: center
        _make_crab_body(left_eye_col=4, right_eye_col=7),  # f3: look right
    ],

    # Eyes scanning left-center-right (4 frames)
    "reading": [
        _make_crab_body(left_eye_col=3, right_eye_col=6),  # f0: center
        _make_crab_body(left_eye_col=2, right_eye_col=5),  # f1: look left
        _make_crab_body(left_eye_col=3, right_eye_col=6),  # f2: center
        _make_crab_body(left_eye_col=4, right_eye_col=7),  # f3: look right
    ],

    # Progress bar sweeping body (4 frames)
    "writing": [
        _make_crab_body(bar_cols=0),   # f0: no bar
        _make_crab_body(bar_cols=2),   # f1: ~33%
        _make_crab_body(bar_cols=4),   # f2: ~66%
        _make_crab_body(bar_cols=6),   # f3: 100%
    ],

    # Claws opening/closing, body shaking (4 frames, shake via window motion)
    "executing": [
        _make_claw_frame(left_claw_open=True, right_claw_open=True),    # f0: both open
        _make_claw_frame(left_claw_open=False, right_claw_open=False),  # f1: both closed
        _make_claw_frame(left_claw_open=True, right_claw_open=True),    # f2: both open
        _make_claw_frame(left_claw_open=False, right_claw_open=False),  # f3: both closed
    ],

    # Red eyes flashing on/off (2 frames)
    "waiting": [
        _make_crab_body(eye_color=R),  # f0: red eyes on
        _make_crab_body(eye_color=O),  # f1: eyes off
    ],
}

# Milliseconds between frame advances per state
FRAME_INTERVALS = {
    "unconfigured": 1000,
    "idle":         600,
    "thinking":     150,
    "reading":      300,
    "writing":      200,
    "executing":    80,
    "waiting":      400,
}

# Window motion type per state (applied by pet.py)
STATE_MOTION = {
    "unconfigured": "none",
    "idle":         "float",
    "thinking":     "tremble",
    "reading":      "none",
    "writing":      "none",
    "executing":    "shake",
    "waiting":      "none",
}
