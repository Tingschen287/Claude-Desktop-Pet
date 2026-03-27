# Claude Desktop Pet — Design Spec

**Date:** 2026-03-27
**Status:** Approved

---

## Overview

A cross-platform (Windows + macOS) floating desktop pet built with Python + PyQt6. The pet uses Claude's logo (orange gradient diamond) as its visual identity, rendered as pixel art using colored rectangles. It monitors an active Claude Code session and animates according to what Claude is currently doing, so the user can stay aware of Claude's status while working on other tasks.

---

## Goals

1. Display a persistent floating pixel-art pet on the desktop that reflects Claude Code's real-time state.
2. Notify the user (via system notification + visual change) when Claude Code requires confirmation.
3. Support user-selectable project monitoring via a simple in-pet UI.
4. Work on both Windows and macOS without requiring Python to be pre-installed (PyInstaller bundle).

---

## Architecture

### State Flow

```
Claude Code Session
      │
      │  Hooks (PreToolUse / PostToolUse / Notification / Stop)
      ▼
scripts/hook_writer.py  ──writes──▶  ~/.claude/pet-state.json
                                              │
                                      polls every 500ms
                                              │
                                         src/pet.py
                                    (PyQt6 floating window)
                                              │
                             ┌────────────────┼───────────────┐
                         renderer.py      animator.py     notifier.py
                        (QPainter blocks) (state machine)  (OS notify)
```

### State File Schema

`~/.claude/pet-state.json`:
```json
{
  "state": "reading",
  "tool": "Read",
  "project": "/Users/admin/myproject",
  "timestamp": 1774599578
}
```

### Config File Schema

`~/.claude/pet-config.json`:
```json
{
  "project": "/Users/admin/myproject"
}
```

Written by `setup_hooks.py` on first project selection. Read by `pet.py` on startup to restore last project. Absence of this file → `unconfigured` state.

---

## States & Animations

| State | Trigger | Eye Color | Animation |
|---|---|---|---|
| `unconfigured` | No `pet-config.json` or invalid project path | Dark gray | Static, dim orange, no movement |
| `idle` | PostToolUse / Stop / stale >30s | White | Slow float, occasional blink |
| `thinking` | PreToolUse: Agent, or any tool whose name starts with "Task" | Purple | Eyes spin, gentle tremble |
| `reading` | PreToolUse: Read / Glob / Grep | Yellow | Eyes scan left-right |
| `writing` | PreToolUse: Edit / Write | Green | Eyes blink, progress bar flows at bottom |
| `executing` | PreToolUse: Bash | Wide yellow | Fast shake |
| `waiting` | Notification hook | Red flashing | Red flash + OS system notification |

**Stale window behavior:** When `timestamp` has not changed for 0–30s (hooks stopped firing but timeout not yet reached), the pet continues showing its last state. After 30s of no update, it transitions to `idle`. This is acceptable given the polling-based design.

### Hook → State Mapping (in `hook_writer.py`)

```
PreToolUse   +  tool ∈ {Read, Glob, Grep}   →  reading
PreToolUse   +  tool ∈ {Edit, Write}         →  writing
PreToolUse   +  tool = Bash                  →  executing
PreToolUse   +  tool == "Agent" or tool.startswith("Task")  →  thinking
PostToolUse  +  any tool                     →  idle
Notification                                 →  waiting
Stop                                         →  idle
```

---

## Hook Configuration

`setup_hooks.py` merges the following fragment into the project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "/absolute/path/to/python /absolute/path/to/hook_writer.py"
      }]
    }],
    "PostToolUse": [{
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "/absolute/path/to/python /absolute/path/to/hook_writer.py"
      }]
    }],
    "Notification": [{
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "/absolute/path/to/python /absolute/path/to/hook_writer.py"
      }]
    }],
    "Stop": [{
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "/absolute/path/to/python /absolute/path/to/hook_writer.py"
      }]
    }]
  }
}
```

**Platform path resolution:** `setup_hooks.py` must substitute the actual paths at installation time using `sys.executable` (Python interpreter) and `os.path.abspath(__file__)` resolved relative to `hook_writer.py`. This is required because:
- On Windows, `~` is not reliably expanded by the shell Claude Code uses to invoke hooks.
- `python` may not be on `PATH` (could be `py`, `python3`, or a venv binary).
- The command string must use the same interpreter that installed the package.

**Idempotent merge:** Before inserting any hook entry, `setup_hooks.py` checks whether a command string containing the `hook_writer.py` path already exists in the target array. If found, it skips insertion. This prevents duplicate hook entries on repeated runs.

### `hook_writer.py` Invocation Contract

Claude Code calls hook scripts by piping a JSON payload to **stdin**. The script reads `sys.stdin`, parses JSON, determines the state, and writes `pet-state.json`.

**Stdin payload format by hook type:**

```json
// PreToolUse / PostToolUse
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Read",
  "tool_input": { ... }
}

// Notification
{
  "hook_event_name": "Notification",
  "message": "Claude needs your input"
}

// Stop
{
  "hook_event_name": "Stop"
}
```

The script reads `payload["hook_event_name"]` to determine the event type and `payload.get("tool_name", "")` to map to a state.

**Error handling contract:** `hook_writer.py` must always exit with code `0`. All exceptions must be caught and logged to `stderr` only. An unhandled exception exiting non-zero may interrupt the Claude Code session.

---

## Pixel Art Design

Based on user-provided pixel matrix (6 rows × 8 columns, 0-indexed):

```
Row 0:  . . O O O O . .
Row 1:  . O O O O O O .
Row 2:  O O E O O E O O   ← E = eye pixel, col=2 and col=5
Row 3:  O O O O O O O O
Row 4:  O O O O O O O O
Row 5:  . O O . . O O .
```

- `O` = orange (#FF6432), `.` = transparent, `E` = eye pixel (color varies by state, default white #FFFFFF)
- Eye positions: `(row=2, col=2)` and `(row=2, col=5)` (0-indexed)
- Each pixel renders as a `QRect` of configurable size (default 12×12px, 1px gap)

### `frames.py` Format

Each state's animation is a list of frame dicts. Each frame is a list of 6 rows, each row containing 8 color strings (`"#RRGGBB"` or `"transparent"`):

```python
# assets/frames.py
TRANSPARENT = "transparent"
ORANGE = "#FF6432"
WHITE = "#FFFFFF"
# ...

FRAMES = {
    "idle": [
        # frame 0
        [
          [TRANSPARENT, TRANSPARENT, ORANGE, ORANGE, ORANGE, ORANGE, TRANSPARENT, TRANSPARENT],
          [TRANSPARENT, ORANGE,      ORANGE, ORANGE, ORANGE, ORANGE, ORANGE,      TRANSPARENT],
          [ORANGE,      ORANGE,      WHITE,  ORANGE, ORANGE, WHITE,  ORANGE,      ORANGE     ],
          [ORANGE,      ORANGE,      ORANGE, ORANGE, ORANGE, ORANGE, ORANGE,      ORANGE     ],
          [ORANGE,      ORANGE,      ORANGE, ORANGE, ORANGE, ORANGE, ORANGE,      ORANGE     ],
          [TRANSPARENT, ORANGE,      ORANGE, TRANSPARENT, TRANSPARENT, ORANGE, ORANGE, TRANSPARENT],
        ],
        # frame 1: eye blink (eye row becomes orange)
        # ...
    ],
    "reading": [...],
    "writing": [...],
    "executing": [...],
    "thinking": [...],
    "waiting": [...],
    "unconfigured": [...],  # all orange replaced with dark #442211
}
```

`animator.py` iterates frames on a `QTimer`, advancing the frame index at a state-specific interval.

---

## UX Flow

### First Launch
1. App opens → pet appears in bottom-right corner in `unconfigured` state (dim colors, static).
2. User **left-clicks** the pet → small settings popup appears.
3. Popup shows: folder picker ("选择项目文件夹") + confirm button.
4. On confirm: `setup_hooks.py` injects hooks into the selected project's `.claude/settings.json`, saves project path to `~/.claude/pet-config.json`, pet transitions to `idle`.

### Daily Use
- Pet floats on desktop, always on top, draggable by left-click-drag.
- Automatically updates state as Claude Code works.
- **Right-click** → context menu:
  - 📁 Current project name (display only)
  - 切换项目…
  - 移除当前项目 Hooks
  - 退出

### CLI Override
```bash
python src/pet.py --project /path/to/project
```
When `--project` is passed, the pet skips the first-launch popup, saves the path to `pet-config.json`, and runs `setup_hooks.py` automatically before starting. Idempotent if hooks are already installed.

### UI Language
Fixed Chinese (simplified). No i18n in v1.

---

## Project Structure

```
Claude-Desktop-Pet/
├── src/
│   ├── pet.py            # Main entry: PyQt6 window, 500ms poll loop, click/drag/menu
│   ├── renderer.py       # Pixel matrix → QPainter colored rectangles
│   ├── animator.py       # State machine: frame sequences, transitions, timing
│   └── notifier.py       # OS notifications (plyer, defensive try/except)
├── scripts/
│   ├── hook_writer.py    # Reads stdin JSON from Claude Code hooks; writes pet-state.json
│   └── setup_hooks.py    # CLI: inject/remove hooks from a project's .claude/settings.json
├── assets/
│   └── frames.py         # All pixel frame data as Python constants (format defined above)
├── requirements.txt      # PyQt6, plyer
└── README.md
```

---

## Key Implementation Notes

- **Transparency:** `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint` + `WA_TranslucentBackground`. Paint background as fully transparent; only pixel blocks are opaque.
- **Drag:** Override `mousePressEvent` / `mouseMoveEvent` on the window for free dragging.
- **Poll timer:** `QTimer` at 500ms reads `pet-state.json`; if `timestamp` unchanged for >30s, treat as `idle`.
- **Hook script safety:** `hook_writer.py` writes atomically: write to a `.tmp` file in the **same directory** as `pet-state.json`, then call `os.replace()` (not `os.rename()`). `os.replace()` is used because on Windows it handles the case where the destination file already exists, unlike `os.rename()`. Always exits 0.
- **Notifier safety:** All calls in `notifier.py` wrapped in `try/except`; notification failure must never crash the pet.
- **setup_hooks.py:** Reads existing `.claude/settings.json`, merges hooks entries (does not overwrite unrelated config), writes back. Idempotent — safe to run multiple times.
- **Packaging:** `pyinstaller --onefile --windowed src/pet.py` + `scripts/` bundled as data files. `hook_writer.py` installed to `~/.claude/pet/scripts/` at first run so Claude Code hooks can call it without the full bundle path.

---

## Out of Scope (v1)

- Multiple simultaneous session monitoring
- Web dashboard / history view
- Custom pixel art themes
- Sound effects
- Auto-start on system boot (post-v1)
