# tests/test_skin_registry.py
# Tests for the skin registry system.

import pytest
from skin_registry import SkinRegistry, SkinModule


def test_registry_has_default_skin():
    """Registry should have the default cat skin."""
    registry = SkinRegistry()
    skin_ids = registry.get_skin_ids()
    assert "default" in skin_ids


def test_registry_has_crab_skin():
    """Registry should have the crab skin."""
    registry = SkinRegistry()
    skin_ids = registry.get_skin_ids()
    assert "crab" in skin_ids


def test_get_default_skin():
    """Get the default skin and verify its properties."""
    registry = SkinRegistry()
    skin = registry.get_skin("default")
    assert skin.id == "default"
    assert skin.name == "小橘猫"
    assert skin.rows == 6
    assert skin.cols == 8
    assert "idle" in skin.frames
    assert "thinking" in skin.frames
    assert "reading" in skin.frames
    assert "writing" in skin.frames
    assert "executing" in skin.frames
    assert "waiting" in skin.frames
    assert "unconfigured" in skin.frames


def test_get_crab_skin():
    """Get the crab skin and verify its properties."""
    registry = SkinRegistry()
    skin = registry.get_skin("crab")
    assert skin.id == "crab"
    assert skin.name == "螃蟹"
    assert skin.rows == 6
    assert skin.cols == 10
    assert len(skin.frames["idle"]) == 4  # blink animation


def test_get_unknown_skin_returns_default():
    """Requesting an unknown skin should return default."""
    registry = SkinRegistry()
    skin = registry.get_skin("nonexistent")
    assert skin.id == "default"


def test_skin_has_all_required_states():
    """Each skin should have all required states."""
    registry = SkinRegistry()
    required_states = ["unconfigured", "idle", "thinking", "reading", "writing", "executing", "waiting"]

    for skin in registry.list_skins():
        for state in required_states:
            assert state in skin.frames, f"Skin {skin.id} missing state: {state}"
            assert len(skin.frames[state]) > 0, f"Skin {skin.id} has empty frames for: {state}"


def test_skin_has_intervals_and_motion():
    """Each skin should have frame intervals and motion types for all states."""
    registry = SkinRegistry()
    required_states = ["unconfigured", "idle", "thinking", "reading", "writing", "executing", "waiting"]

    for skin in registry.list_skins():
        for state in required_states:
            assert state in skin.frame_intervals, f"Skin {skin.id} missing interval for: {state}"
            assert state in skin.state_motion, f"Skin {skin.id} missing motion for: {state}"
            # Verify motion type is valid
            assert skin.state_motion[state] in ["float", "shake", "tremble", "none"]


def test_list_skins():
    """List all skins should return all available skins."""
    registry = SkinRegistry()
    skins = registry.list_skins()
    skin_ids = {s.id for s in skins}
    assert "default" in skin_ids
    assert "crab" in skin_ids
