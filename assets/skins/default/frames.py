# assets/skins/default/frames.py
# Default cat skin frame data for the Claude Desktop Pet.
# Grid: 6 rows x 8 columns. Colors are "#RRGGBB" or "transparent".
# Eye positions (row=2): left=col2, right=col5.

T = "transparent"
O = "#FF6432"  # Orange (body)
W = "#FFFFFF"  # White (idle eye)
P = "#AA44FF"  # Purple (thinking eye)
Y = "#FFDD44"  # Yellow (reading/executing eye)
G = "#44FF88"  # Green (writing eye)
R = "#FF3344"  # Red (waiting eye)
D = "#442211"  # Dim orange (unconfigured body)
DE = "#553322"  # Dim eye (unconfigured)


def _row0(c=O):
    return [T, T, c, c, c, c, T, T]


def _row1(c=O):
    return [T, c, c, c, c, c, c, T]


def _row3(c=O):
    return [c, c, c, c, c, c, c, c]


def _row5(c=O):
    return [T, c, c, T, T, c, c, T]


def _make_frame(eye_color, lc=2, rc=5, bar_cols=0, body=O):
    """Build one 6x8 frame. lc/rc = left/right eye column (0-indexed)."""
    row2 = [body] * 8
    row2[lc] = eye_color
    row2[rc] = eye_color
    row4 = [body] * 8
    for i in range(1, 1 + bar_cols):
        row4[i] = G
    return [
        _row0(body),
        _row1(body),
        row2,
        _row3(body),
        row4,
        _row5(body),
    ]


def _make_wide_frame(eye_color, left_cols, right_cols, body=O):
    """Wide eyes: multiple columns per eye."""
    row2 = [body] * 8
    for c in left_cols:
        row2[c] = eye_color
    for c in right_cols:
        row2[c] = eye_color
    return [
        _row0(body),
        _row1(body),
        row2,
        _row3(body),
        _row3(body),
        _row5(body),
    ]


FRAMES = {
    # Static dim appearance - no animation
    "unconfigured": [
        _make_frame(DE, body=D),
    ],

    # White eyes, slow blink cycle (4 frames)
    "idle": [
        _make_frame(W),        # f0: eyes open
        _make_frame(W),        # f1: eyes open (hold)
        _make_frame(O),        # f2: blink closed
        _make_frame(W),        # f3: eyes reopen
    ],

    # Purple eyes shifting left-center-right (4 frames)
    "thinking": [
        _make_frame(P, 2, 5),  # f0: center
        _make_frame(P, 1, 4),  # f1: left
        _make_frame(P, 2, 5),  # f2: center
        _make_frame(P, 3, 6),  # f3: right
    ],

    # Yellow eyes scanning left-center-right (4 frames)
    "reading": [
        _make_frame(Y, 2, 5),  # f0: center
        _make_frame(Y, 1, 4),  # f1: look left
        _make_frame(Y, 2, 5),  # f2: center
        _make_frame(Y, 3, 6),  # f3: look right
    ],

    # Green eyes + progress bar sweeping row 4 (4 frames)
    "writing": [
        _make_frame(G, bar_cols=0),  # f0: no bar
        _make_frame(G, bar_cols=2),  # f1: 25%
        _make_frame(G, bar_cols=4),  # f2: 50%
        _make_frame(G, bar_cols=6),  # f3: 75%
    ],

    # Wide yellow eyes alternating (4 frames, shake via window motion)
    "executing": [
        _make_wide_frame(Y, [1, 2], [4, 5]),  # f0: wide left
        _make_wide_frame(Y, [2, 3], [5, 6]),  # f1: wide right
        _make_wide_frame(Y, [1, 2], [4, 5]),  # f2: wide left
        _make_wide_frame(Y, [2, 3], [5, 6]),  # f3: wide right
    ],

    # Red eyes flashing on/off (2 frames)
    "waiting": [
        _make_frame(R, 2, 5),  # f0: red eyes on
        _make_frame(O, 2, 5),  # f1: eyes off
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
