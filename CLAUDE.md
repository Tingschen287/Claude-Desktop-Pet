# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A floating desktop pet (PyQt6) that watches a Claude Code session and animates based on what Claude is doing. It uses Claude's hooks system to receive real-time events, writes a state file, and the pet window polls that file to animate accordingly.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run the pet
python src/pet.py
python src/pet.py --project /path/to/project

# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_setup_hooks.py -v

# Run a single test
python -m pytest tests/test_setup_hooks.py::test_inject_is_idempotent -v
```

## Architecture

### Data Flow

```
Claude Code session
  → hooks fire (PreToolUse / PostToolUse / Notification / Stop)
  → scripts/hook_writer.py reads stdin JSON, writes ~/.claude/pet-state.json
  → src/pet.py polls pet-state.json every 500ms
  → PetAnimator transitions state → PetRenderer draws pixel frames
```

### Key Files

| File | Role |
|------|------|
| `src/pet.py` | Main PyQt6 window. Owns the poll timer, drag logic, right-click menu, and project config. |
| `src/animator.py` | State machine. Holds current state, advances frame index on QTimer, emits `frame_changed` and `motion_changed` signals. |
| `src/renderer.py` | Draws a 6×8 pixel grid using `QPainter.fillRect`. Each cell is 12×12px with 1px gap. |
| `src/notifier.py` | Thin wrapper around `plyer.notification`. All exceptions silently swallowed. |
| `assets/frames.py` | All pixel frame data as Python lists. `FRAMES[state]` = list of frames. `FRAME_INTERVALS[state]` = ms per frame. `STATE_MOTION[state]` = window motion type. |
| `scripts/hook_writer.py` | Called by Claude Code hooks via stdin pipe. Reads JSON payload, maps event+tool to a state string, atomically writes `pet-state.json` via `os.replace()`. Always exits 0. |
| `scripts/setup_hooks.py` | Injects/removes hook entries in a project's `.claude/settings.json`. Idempotent. |

### States

`unconfigured` → no project configured; `idle` → PostToolUse/Stop/stale >30s; `thinking` → Agent/Task tools; `reading` → Read/Glob/Grep; `writing` → Edit/Write; `executing` → Bash; `waiting` → Notification hook event.

### Hook Config Format

`setup_hooks.py` writes to `.claude/settings.json` in this structure:
```json
{
  "hooks": {
    "PreToolUse": [{"matcher": "", "hooks": [{"type": "command", "command": "python /abs/path/hook_writer.py"}]}],
    "PostToolUse": [...],
    "Notification": [...],
    "Stop": [...]
  }
}
```

### Runtime Files

- `~/.claude/pet-state.json` — written by `hook_writer.py`, read by `pet.py`
- `~/.claude/pet-config.json` — stores `{"project": "/abs/path"}`, written by `pet.py` on project selection

### Window Motion

`STATE_MOTION` in `frames.py` maps states to motion types (`float`, `shake`, `tremble`, `none`). `PetWindow._apply_motion` drives the motion via a 50ms QTimer that offsets the window position from `_base_pos`.

## Adding a New State

1. Add color constants and frames to `assets/frames.py` under `FRAMES["new_state"]`
2. Add an entry in `FRAME_INTERVALS` and `STATE_MOTION`
3. Map hook event/tool to the new state in `scripts/hook_writer.py`
4. The animator and renderer pick it up automatically — no other changes needed

## Specs and Plans

Design docs live in `docs/superpowers/specs/`. Implementation plans live in `docs/superpowers/plans/`. Read these before making architectural changes.
