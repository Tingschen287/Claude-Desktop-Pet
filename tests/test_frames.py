import re
import pytest
from frames import FRAMES, FRAME_INTERVALS, STATE_MOTION

REQUIRED_STATES = {"unconfigured", "idle", "thinking", "reading", "writing", "executing", "waiting"}
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def test_all_states_present():
    assert set(FRAMES.keys()) == REQUIRED_STATES


def test_frame_intervals_present():
    for state in REQUIRED_STATES:
        assert state in FRAME_INTERVALS, f"Missing interval for {state}"
        assert isinstance(FRAME_INTERVALS[state], int)
        assert FRAME_INTERVALS[state] > 0


def test_state_motion_present():
    valid_motions = {"none", "float", "shake", "tremble"}
    for state in REQUIRED_STATES:
        assert state in STATE_MOTION, f"Missing motion for {state}"
        assert STATE_MOTION[state] in valid_motions


def test_frame_dimensions():
    for state, frames_list in FRAMES.items():
        assert len(frames_list) >= 1, f"{state}: needs at least 1 frame"
        for i, frame in enumerate(frames_list):
            assert len(frame) == 6, f"{state} frame {i}: expected 6 rows, got {len(frame)}"
            for j, row in enumerate(frame):
                assert len(row) == 8, f"{state} frame {i} row {j}: expected 8 cols, got {len(row)}"


def test_color_values_valid():
    for state, frames_list in FRAMES.items():
        for i, frame in enumerate(frames_list):
            for j, row in enumerate(frame):
                for k, color in enumerate(row):
                    assert color == "transparent" or HEX_RE.match(color), (
                        f"Invalid color '{color}' at {state} frame {i} row {j} col {k}"
                    )


def test_unconfigured_has_one_frame():
    assert len(FRAMES["unconfigured"]) == 1


def test_waiting_has_two_frames():
    assert len(FRAMES["waiting"]) == 2
