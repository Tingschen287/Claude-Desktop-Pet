# assets/skins/crab/frames.py
# Crab skin frame data for Claude Desktop Pet.
# Grid: 10 rows x 16 columns. Colors are "#RRGGBB" or "transparent".

T = "transparent"  # Transparent
O = "#FF6432"  # Orange (body) - same as default cat skin
B = "#000000"  # Black (eyes)
G = "#44FF88"  # Green (writing progress bar)
R = "#FF3344"  # Red (waiting eye flash)
D = "#442211"  # Dim orange (unconfigured body) - same as default cat skin
DE = "#553322"  # Dim eye (unconfigured) - same as default cat skin


def _make_crab_body(body=O, eye_color=B, left_eye_col=5, right_eye_col=10, bar_cols=0):
    """Build one 10x16 crab frame."""
    # Row 0-1: Body top (rows 0-1)
    row0 = [T] + [body] * 14 + [T]
    row1 = [T] + [body] * 14 + [T]

    # Row 2-3: Eyes (eyes are 2 rows deep, at golden ratio position)
    row2 = [body] * 16
    row2[left_eye_col] = eye_color
    row2[right_eye_col] = eye_color
    row3 = [body] * 16
    row3[left_eye_col] = eye_color
    row3[right_eye_col] = eye_color

    # Row 4-7: Body bottom (full, no gaps)
    row4 = [T] + [body] * 14 + [T]
    # Row 5 has progress bar for writing state
    row5 = [T] + [body] * 14 + [T]
    if bar_cols > 0:
        # Progress bar in middle of body
        bar_start = 3
        for i in range(bar_cols):
            if bar_start + i < 13:
                row5[bar_start + i] = G

    row6 = [T] + [body] * 14 + [T]
    row7 = [T] + [body] * 14 + [T]

    # Row 8: Gap between body and legs
    row8 = [T] * 16

    # Row 9-10: Legs (two groups, each with 2 columns)
    row9 = [T, T, T, body, T, body, T, T, T, T, body, T, body, T, T, T]
    row10 = [T, T, T, body, T, body, T, T, T, T, body, T, body, T, T, T]

    return [row0, row1, row2, row3, row4, row5, row6, row7, row8, row9, row10]


def _make_claw_frame(body=O, eye_color=B, left_claw_open=True, right_claw_open=True, left_eye_col=5, right_eye_col=10):
    """Build crab frame with animated claws."""
    frame = _make_crab_body(body, eye_color, left_eye_col, right_eye_col)

    # Row 0-1: Add claws at edges
    if left_claw_open:
        frame[0][0] = body
        frame[0][1] = body
        frame[1][0] = body
    if right_claw_open:
        frame[0][14] = body
        frame[0][15] = body
        frame[1][15] = body

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
        _make_crab_body(left_eye_col=5, right_eye_col=10),  # f0: center
        _make_crab_body(left_eye_col=4, right_eye_col=9),   # f1: look left
        _make_crab_body(left_eye_col=5, right_eye_col=10),  # f2: center
        _make_crab_body(left_eye_col=6, right_eye_col=11),  # f3: look right
    ],

    # Eyes scanning left-center-right (4 frames)
    "reading": [
        _make_crab_body(left_eye_col=5, right_eye_col=10),  # f0: center
        _make_crab_body(left_eye_col=4, right_eye_col=9),   # f1: look left
        _make_crab_body(left_eye_col=5, right_eye_col=10),  # f2: center
        _make_crab_body(left_eye_col=6, right_eye_col=11),  # f3: look right
    ],

    # Progress bar sweeping body (4 frames)
    "writing": [
        _make_crab_body(bar_cols=0),   # f0: no bar
        _make_crab_body(bar_cols=3),   # f1: ~25%
        _make_crab_body(bar_cols=6),   # f2: ~50%
        _make_crab_body(bar_cols=9),   # f3: ~75%
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
