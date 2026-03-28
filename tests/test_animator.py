import pytest
from animator import PetAnimator


def test_default_state_is_unconfigured(qapp):
    a = PetAnimator()
    assert a.state == "unconfigured"


def test_set_state_changes_state(qapp):
    a = PetAnimator()
    a.set_state("reading")
    assert a.state == "reading"


def test_unknown_state_falls_back_to_unconfigured(qapp):
    a = PetAnimator()
    a.set_state("nonexistent_state")
    assert a.state == "unconfigured"


def test_current_frame_has_correct_dimensions(qapp):
    a = PetAnimator()
    a.set_state("idle")
    frame = a.current_frame()
    assert len(frame) == 6
    assert all(len(row) == 8 for row in frame)


def test_same_state_does_not_reset_frame_index(qapp):
    a = PetAnimator()
    a.set_state("reading")
    a._frame_index = 2
    a.set_state("reading")
    assert a._frame_index == 2


def test_different_state_resets_frame_index(qapp):
    a = PetAnimator()
    a.set_state("reading")
    a._frame_index = 2
    a.set_state("writing")
    assert a._frame_index == 0


def test_advance_frame_cycles(qapp):
    a = PetAnimator()
    a.set_state("idle")  # idle has 4 frames
    a._frame_index = 3
    a._advance_frame()
    assert a._frame_index == 0


def test_stop_does_not_raise(qapp):
    a = PetAnimator()
    a.set_state("idle")
    a.stop()
