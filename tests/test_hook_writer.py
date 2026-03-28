import json
import os
import pytest
from hook_writer import determine_state, write_state


def test_pre_tool_read_maps_to_reading():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "Read"}) == "reading"


def test_pre_tool_glob_maps_to_reading():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "Glob"}) == "reading"


def test_pre_tool_grep_maps_to_reading():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "Grep"}) == "reading"


def test_pre_tool_edit_maps_to_writing():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "Edit"}) == "writing"


def test_pre_tool_write_maps_to_writing():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "Write"}) == "writing"


def test_pre_tool_bash_maps_to_executing():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "Bash"}) == "executing"


def test_pre_tool_agent_maps_to_thinking():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "Agent"}) == "thinking"


def test_pre_tool_taskcreate_maps_to_thinking():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "TaskCreate"}) == "thinking"


def test_pre_tool_taskupdate_maps_to_thinking():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "TaskUpdate"}) == "thinking"


def test_pre_tool_unknown_maps_to_thinking():
    assert determine_state({"hook_event_name": "PreToolUse", "tool_name": "SomeFutureTool"}) == "thinking"


def test_post_tool_maps_to_idle():
    assert determine_state({"hook_event_name": "PostToolUse", "tool_name": "Read"}) == "idle"


def test_notification_maps_to_waiting():
    assert determine_state({"hook_event_name": "Notification"}) == "waiting"


def test_stop_maps_to_idle():
    assert determine_state({"hook_event_name": "Stop"}) == "idle"


def test_empty_payload_maps_to_idle():
    assert determine_state({}) == "idle"


def test_write_state_creates_file(tmp_path, monkeypatch):
    state_file = str(tmp_path / "pet-state.json")
    monkeypatch.setattr("hook_writer.STATE_FILE", state_file)
    write_state("reading", tool="Read")
    data = json.loads(open(state_file).read())
    assert data["state"] == "reading"
    assert data["tool"] == "Read"
    assert "timestamp" in data


def test_write_state_is_atomic(tmp_path, monkeypatch):
    state_file = str(tmp_path / "pet-state.json")
    monkeypatch.setattr("hook_writer.STATE_FILE", state_file)
    write_state("idle")
    tmp_file = state_file + ".tmp"
    assert not os.path.exists(tmp_file)
