# Claude Desktop Pet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a floating PyQt6 desktop pet that renders Claude's logo as pixel art and animates according to Claude Code session state.

**Architecture:** Claude Code hooks pipe JSON to `hook_writer.py`, which writes `~/.claude/pet-state.json`. `pet.py` polls that file every 500ms and drives the `PetAnimator` state machine, which emits frame updates to `PetRenderer` for QPainter drawing.

**Tech Stack:** Python 3.10+, PyQt6, plyer, pytest

---

## File Map

| File | Responsibility |
|---|---|
| `assets/frames.py` | All pixel frame data (6×8 color grids) + timing + motion constants |
| `src/renderer.py` | `PetRenderer`: converts a frame (list of rows) into QPainter `fillRect` calls |
| `src/animator.py` | `PetAnimator(QObject)`: state machine + QTimer frame cycling |
| `src/notifier.py` | `send_notification()`: defensive OS notification wrapper |
| `scripts/hook_writer.py` | Reads Claude Code hook stdin JSON → writes `~/.claude/pet-state.json` |
| `scripts/setup_hooks.py` | `install_hooks()` / `remove_hooks()`: merges hook config into `.claude/settings.json` |
| `src/pet.py` | `PetWindow(QWidget)`: transparent floating window, polling, drag, context menu |
| `tests/conftest.py` | pytest path setup + QApplication fixture |
| `tests/test_frames.py` | Validates frame structure and color values |
| `tests/test_animator.py` | Tests state transitions and frame cycling |
| `tests/test_hook_writer.py` | Tests stdin parsing and state mapping |
| `tests/test_setup_hooks.py` | Tests hook JSON merge, idempotency, and removal |

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.gitignore`
- Create: `assets/__init__.py`
- Create: `src/__init__.py`
- Create: `scripts/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src scripts assets tests
touch assets/__init__.py src/__init__.py scripts/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write `requirements.txt`**

```
PyQt6>=6.4.0
plyer>=2.1.0
```

- [ ] **Step 3: Write `requirements-dev.txt`**

```
pytest>=7.0.0
```

- [ ] **Step 4: Write `.gitignore`**

```
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
*.spec
.venv/
venv/
.superpowers/
```

- [ ] **Step 5: Write `tests/conftest.py`**

```python
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "assets"))


@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
```

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Expected: packages install without error.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt requirements-dev.txt .gitignore assets/__init__.py src/__init__.py scripts/__init__.py tests/__init__.py tests/conftest.py
git commit -m "[AI开发]chore(scaffold): 初始化项目目录结构和依赖配置"
```

---

## Task 2: Pixel Frame Data (`assets/frames.py`)

**Files:**
- Create: `assets/frames.py`
- Create: `tests/test_frames.py`

- [ ] **Step 1: Write `tests/test_frames.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_frames.py -v
```

Expected: `ModuleNotFoundError: No module named 'frames'`

- [ ] **Step 3: Write `assets/frames.py`**

```python
# assets/frames.py
# All pixel frame data for the Claude Desktop Pet.
# Grid: 6 rows × 8 columns. Colors are "#RRGGBB" or "transparent".
# Eye positions (row=2): left=col2, right=col5.

T = "transparent"
O = "#FF6432"  # Orange (body)
W = "#FFFFFF"  # White (idle eye)
P = "#AA44FF"  # Purple (thinking eye)
Y = "#FFDD44"  # Yellow (reading eye)
G = "#44FF88"  # Green (writing eye)
R = "#FF3344"  # Red (waiting eye)
D = "#442211"  # Dim orange (unconfigured body)
DE = "#553322" # Dim eye (unconfigured)


def _row0(c=O): return [T, T, c, c, c, c, T, T]
def _row1(c=O): return [T, c, c, c, c, c, c, T]
def _row3(c=O): return [c, c, c, c, c, c, c, c]
def _row4(c=O, bar_cols=0, bar_color=G):
    row = [c] * 8
    for i in range(1, 1 + bar_cols):
        row[i] = bar_color
    return row
def _row5(c=O): return [T, c, c, T, T, c, c, T]


def _make_frame(eye_color, lc=2, rc=5, bar_cols=0, body=O):
    """Build one 6×8 frame. lc/rc = left/right eye column (0-indexed)."""
    row2 = [body] * 8
    row2[lc] = eye_color
    row2[rc] = eye_color
    return [
        _row0(body),
        _row1(body),
        row2,
        _row3(body),
        _row4(body, bar_cols),
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
        _row4(body),
        _row5(body),
    ]


FRAMES = {
    # Static dim appearance — no animation
    "unconfigured": [
        _make_frame(DE, body=D),
    ],

    # White eyes, slow blink cycle (4 frames)
    "idle": [
        _make_frame(W),             # f0: eyes open
        _make_frame(W),             # f1: eyes open (hold longer via repeat)
        _make_frame(O),             # f2: blink (eyes = body color = invisible)
        _make_frame(W),             # f3: eyes reopen
    ],

    # Purple eyes shifting left-center-right (4 frames)
    "thinking": [
        _make_frame(P, 2, 5),       # f0: center
        _make_frame(P, 1, 4),       # f1: left
        _make_frame(P, 2, 5),       # f2: center
        _make_frame(P, 3, 6),       # f3: right
    ],

    # Yellow eyes scanning left-center-right (4 frames)
    "reading": [
        _make_frame(Y, 2, 5),       # f0: center
        _make_frame(Y, 1, 4),       # f1: look left
        _make_frame(Y, 2, 5),       # f2: center
        _make_frame(Y, 3, 6),       # f3: look right
    ],

    # Green eyes + progress bar sweeping row 4 (4 frames)
    "writing": [
        _make_frame(G, bar_cols=0),  # f0: no bar
        _make_frame(G, bar_cols=2),  # f1: 25%
        _make_frame(G, bar_cols=4),  # f2: 50%
        _make_frame(G, bar_cols=6),  # f3: 75%
    ],

    # Wide yellow eyes alternating position (4 frames, shaking handled by window)
    "executing": [
        _make_wide_frame(Y, [1, 2], [4, 5]),    # f0: wide left
        _make_wide_frame(Y, [2, 3], [5, 6]),    # f1: wide right
        _make_wide_frame(Y, [1, 2], [4, 5]),    # f2: wide left
        _make_wide_frame(Y, [2, 3], [5, 6]),    # f3: wide right
    ],

    # Red eyes flashing on/off (2 frames)
    "waiting": [
        _make_frame(R, 2, 5),       # f0: red eyes on
        _make_frame(O, 2, 5),       # f1: eyes off (same as body)
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_frames.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add assets/frames.py tests/test_frames.py
git commit -m "[AI开发]feat(frames): 新增所有状态的像素帧数据和动画时序配置"
```

---

## Task 3: Renderer (`src/renderer.py`)

**Files:**
- Create: `src/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: Write `tests/test_renderer.py`**

```python
import pytest
from renderer import PetRenderer


def test_widget_width():
    # 8 cols * 12px + 7 gaps * 1px = 103
    assert PetRenderer.widget_width() == 103


def test_widget_height():
    # 6 rows * 12px + 5 gaps * 1px = 77
    assert PetRenderer.widget_height() == 77


def test_render_does_not_raise(qapp):
    from PyQt6.QtGui import QPainter, QPixmap
    from frames import FRAMES

    renderer = PetRenderer()
    pixmap = QPixmap(PetRenderer.widget_width(), PetRenderer.widget_height())
    pixmap.fill()
    painter = QPainter(pixmap)
    frame = FRAMES["idle"][0]
    renderer.render(painter, frame)   # must not raise
    painter.end()


def test_render_skips_transparent(qapp):
    """render() must not crash on transparent pixels."""
    from PyQt6.QtGui import QPainter, QPixmap

    renderer = PetRenderer()
    pixmap = QPixmap(PetRenderer.widget_width(), PetRenderer.widget_height())
    pixmap.fill()
    painter = QPainter(pixmap)
    # Frame with all-transparent cells
    frame = [["transparent"] * 8 for _ in range(6)]
    renderer.render(painter, frame)
    painter.end()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_renderer.py -v
```

Expected: `ModuleNotFoundError: No module named 'renderer'`

- [ ] **Step 3: Write `src/renderer.py`**

```python
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import QRect


class PetRenderer:
    PIXEL_SIZE = 12
    PIXEL_GAP = 1
    COLS = 8
    ROWS = 6

    @classmethod
    def widget_width(cls) -> int:
        return cls.COLS * cls.PIXEL_SIZE + (cls.COLS - 1) * cls.PIXEL_GAP

    @classmethod
    def widget_height(cls) -> int:
        return cls.ROWS * cls.PIXEL_SIZE + (cls.ROWS - 1) * cls.PIXEL_GAP

    def render(self, painter: QPainter, frame: list) -> None:
        """Draw frame onto painter. Transparent cells are skipped."""
        step = self.PIXEL_SIZE + self.PIXEL_GAP
        for row_idx, row in enumerate(frame):
            y = row_idx * step
            for col_idx, color in enumerate(row):
                if color == "transparent":
                    continue
                x = col_idx * step
                painter.fillRect(
                    QRect(x, y, self.PIXEL_SIZE, self.PIXEL_SIZE),
                    QColor(color),
                )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_renderer.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/renderer.py tests/test_renderer.py
git commit -m "[AI开发]feat(renderer): 新增像素渲染器，QPainter 色块绘制"
```

---

## Task 4: Animator (`src/animator.py`)

**Files:**
- Create: `src/animator.py`
- Create: `tests/test_animator.py`

- [ ] **Step 1: Write `tests/test_animator.py`**

```python
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
    a.set_state("reading")   # same state → no reset
    assert a._frame_index == 2


def test_different_state_resets_frame_index(qapp):
    a = PetAnimator()
    a.set_state("reading")
    a._frame_index = 2
    a.set_state("writing")
    assert a._frame_index == 0


def test_advance_frame_cycles(qapp):
    a = PetAnimator()
    a.set_state("idle")      # idle has 4 frames
    a._frame_index = 3
    a._advance_frame()
    assert a._frame_index == 0   # wraps around


def test_stop_does_not_raise(qapp):
    a = PetAnimator()
    a.set_state("idle")
    a.stop()   # must not raise
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_animator.py -v
```

Expected: `ModuleNotFoundError: No module named 'animator'`

- [ ] **Step 3: Write `src/animator.py`**

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "assets"))

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from frames import FRAMES, FRAME_INTERVALS, STATE_MOTION


class PetAnimator(QObject):
    frame_changed = pyqtSignal(list)
    motion_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "unconfigured"
        self._frame_index = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_frame)

    @property
    def state(self) -> str:
        return self._state

    def set_state(self, state: str) -> None:
        if state not in FRAMES:
            state = "unconfigured"
        if state == self._state:
            return
        self._state = state
        self._frame_index = 0
        self._timer.stop()
        if len(FRAMES[state]) > 1:
            self._timer.start(FRAME_INTERVALS.get(state, 600))
        self.frame_changed.emit(self.current_frame())
        self.motion_changed.emit(STATE_MOTION.get(state, "none"))

    def current_frame(self) -> list:
        frames = FRAMES.get(self._state, FRAMES["unconfigured"])
        return frames[self._frame_index % len(frames)]

    def _advance_frame(self) -> None:
        frames = FRAMES.get(self._state, FRAMES["unconfigured"])
        self._frame_index = (self._frame_index + 1) % len(frames)
        self.frame_changed.emit(self.current_frame())

    def start(self) -> None:
        frames = FRAMES.get(self._state, [])
        if len(frames) > 1:
            self._timer.start(FRAME_INTERVALS.get(self._state, 600))

    def stop(self) -> None:
        self._timer.stop()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_animator.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/animator.py tests/test_animator.py
git commit -m "[AI开发]feat(animator): 新增状态机和帧动画驱动器"
```

---

## Task 5: Hook Writer (`scripts/hook_writer.py`)

**Files:**
- Create: `scripts/hook_writer.py`
- Create: `tests/test_hook_writer.py`

- [ ] **Step 1: Write `tests/test_hook_writer.py`**

```python
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
    state_file = tmp_path / "pet-state.json"
    monkeypatch.setattr("hook_writer.STATE_FILE", str(state_file))
    write_state("reading", tool="Read")
    data = json.loads(state_file.read_text())
    assert data["state"] == "reading"
    assert data["tool"] == "Read"
    assert "timestamp" in data


def test_write_state_is_atomic(tmp_path, monkeypatch):
    """Temp file must not remain after write."""
    state_file = tmp_path / "pet-state.json"
    monkeypatch.setattr("hook_writer.STATE_FILE", str(state_file))
    write_state("idle")
    tmp_file = str(state_file) + ".tmp"
    assert not os.path.exists(tmp_file)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_hook_writer.py -v
```

Expected: `ModuleNotFoundError: No module named 'hook_writer'`

- [ ] **Step 3: Write `scripts/hook_writer.py`**

```python
import sys
import json
import os
import time

STATE_FILE = os.path.join(os.path.expanduser("~"), ".claude", "pet-state.json")

_READING_TOOLS = {"Read", "Glob", "Grep"}
_WRITING_TOOLS = {"Edit", "Write"}


def determine_state(payload: dict) -> str:
    """Map a Claude Code hook payload to a pet state string."""
    event = payload.get("hook_event_name", "")
    tool = payload.get("tool_name", "")

    if event == "Notification":
        return "waiting"
    if event in ("PostToolUse", "Stop"):
        return "idle"
    if event == "PreToolUse":
        if tool in _READING_TOOLS:
            return "reading"
        if tool in _WRITING_TOOLS:
            return "writing"
        if tool == "Bash":
            return "executing"
        if tool == "Agent" or tool.startswith("Task"):
            return "thinking"
        return "thinking"
    return "idle"


def write_state(state: str, tool: str = "", project: str = "") -> None:
    """Atomically write state to STATE_FILE using os.replace()."""
    state_dir = os.path.dirname(STATE_FILE)
    os.makedirs(state_dir, exist_ok=True)
    data = {
        "state": state,
        "tool": tool,
        "project": project,
        "timestamp": int(time.time()),
    }
    tmp_file = STATE_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp_file, STATE_FILE)


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        state = determine_state(payload)
        tool = payload.get("tool_name", "")
        write_state(state, tool)
    except Exception as e:
        print(f"[hook_writer] error: {e}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_hook_writer.py -v
```

Expected: all 16 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/hook_writer.py tests/test_hook_writer.py
git commit -m "[AI开发]feat(hook-writer): 新增 Hook 状态写入脚本，解析 Claude Code stdin 并写入状态文件"
```

---

## Task 6: Setup Hooks (`scripts/setup_hooks.py`)

**Files:**
- Create: `scripts/setup_hooks.py`
- Create: `tests/test_setup_hooks.py`

- [ ] **Step 1: Write `tests/test_setup_hooks.py`**

```python
import json
import pytest
from pathlib import Path
from setup_hooks import install_hooks, remove_hooks, _has_hook


def test_install_hooks_creates_all_four_hook_types(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{}")
    install_hooks(str(tmp_path), "/usr/bin/python3", "/path/to/hook_writer.py")
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    for hook_type in ("PreToolUse", "PostToolUse", "Notification", "Stop"):
        assert hook_type in data["hooks"], f"Missing {hook_type}"


def test_install_hooks_embeds_correct_paths(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{}")
    install_hooks(str(tmp_path), "/usr/bin/python3", "/path/to/hook_writer.py")
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    cmd = data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "/usr/bin/python3" in cmd
    assert "/path/to/hook_writer.py" in cmd


def test_install_hooks_is_idempotent(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{}")
    install_hooks(str(tmp_path), "/usr/bin/python3", "/path/to/hook_writer.py")
    install_hooks(str(tmp_path), "/usr/bin/python3", "/path/to/hook_writer.py")
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert len(data["hooks"]["PreToolUse"]) == 1


def test_install_hooks_preserves_existing_settings(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        '{"permissions": {"allow": ["Bash"]}}'
    )
    install_hooks(str(tmp_path), "/usr/bin/python3", "/path/to/hook_writer.py")
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert data["permissions"]["allow"] == ["Bash"]


def test_install_hooks_creates_settings_file_if_missing(tmp_path):
    (tmp_path / ".claude").mkdir()
    install_hooks(str(tmp_path), "/usr/bin/python3", "/path/to/hook_writer.py")
    assert (tmp_path / ".claude" / "settings.json").exists()


def test_remove_hooks_cleans_all_hook_types(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{}")
    install_hooks(str(tmp_path), "/usr/bin/python3", "/path/to/hook_writer.py")
    remove_hooks(str(tmp_path), "/path/to/hook_writer.py")
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    hooks = data.get("hooks", {})
    for hook_list in hooks.values():
        for entry in hook_list:
            for h in entry.get("hooks", []):
                assert "hook_writer.py" not in h.get("command", "")


def test_remove_hooks_preserves_other_settings(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        '{"permissions": {"allow": ["Bash"]}}'
    )
    install_hooks(str(tmp_path), "/usr/bin/python3", "/path/to/hook_writer.py")
    remove_hooks(str(tmp_path), "/path/to/hook_writer.py")
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert data["permissions"]["allow"] == ["Bash"]


def test_has_hook_detects_existing_entry():
    entries = [{"matcher": ".*", "hooks": [{"type": "command", "command": "/py /hook_writer.py"}]}]
    assert _has_hook(entries, "/hook_writer.py") is True


def test_has_hook_returns_false_when_absent():
    entries = [{"matcher": ".*", "hooks": [{"type": "command", "command": "/py /other.py"}]}]
    assert _has_hook(entries, "/hook_writer.py") is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_setup_hooks.py -v
```

Expected: `ModuleNotFoundError: No module named 'setup_hooks'`

- [ ] **Step 3: Write `scripts/setup_hooks.py`**

```python
import sys
import json
import os
import argparse
from pathlib import Path


def _hook_command(python_exe: str, hook_script: str) -> str:
    return f'"{python_exe}" "{hook_script}"'


def _has_hook(hook_list: list, hook_script: str) -> bool:
    """Return True if any entry in hook_list already references hook_script."""
    for entry in hook_list:
        for h in entry.get("hooks", []):
            if hook_script in h.get("command", ""):
                return True
    return False


def _make_hook_entry(python_exe: str, hook_script: str) -> dict:
    return {
        "matcher": ".*",
        "hooks": [{"type": "command", "command": _hook_command(python_exe, hook_script)}],
    }


def install_hooks(project_dir: str, python_exe: str, hook_script: str) -> None:
    """Merge pet hook entries into <project_dir>/.claude/settings.json."""
    settings_path = Path(project_dir) / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists():
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        data = {}

    hooks = data.setdefault("hooks", {})
    entry = _make_hook_entry(python_exe, hook_script)

    for hook_type in ("PreToolUse", "PostToolUse", "Notification", "Stop"):
        hook_list = hooks.setdefault(hook_type, [])
        if not _has_hook(hook_list, hook_script):
            hook_list.append(entry)

    settings_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def remove_hooks(project_dir: str, hook_script: str) -> None:
    """Remove all pet hook entries from <project_dir>/.claude/settings.json."""
    settings_path = Path(project_dir) / ".claude" / "settings.json"
    if not settings_path.exists():
        return

    data = json.loads(settings_path.read_text(encoding="utf-8"))
    hooks = data.get("hooks", {})

    for hook_type in list(hooks.keys()):
        hooks[hook_type] = [
            e for e in hooks[hook_type] if not _has_hook([e], hook_script)
        ]
        if not hooks[hook_type]:
            del hooks[hook_type]

    if not hooks:
        data.pop("hooks", None)

    settings_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Install/remove Claude pet hooks")
    parser.add_argument("--project", required=True, help="Project directory to configure")
    parser.add_argument("--remove", action="store_true", help="Remove hooks instead of installing")
    args = parser.parse_args()

    hook_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "hook_writer.py"))

    if args.remove:
        remove_hooks(args.project, hook_script)
        print(f"Hooks removed from {args.project}")
    else:
        install_hooks(args.project, sys.executable, hook_script)
        print(f"Hooks installed in {args.project}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_setup_hooks.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/setup_hooks.py tests/test_setup_hooks.py
git commit -m "[AI开发]feat(setup-hooks): 新增 Hook 安装/卸载脚本，幂等合并 .claude/settings.json"
```

---

## Task 7: Notifier (`src/notifier.py`)

**Files:**
- Create: `src/notifier.py`

- [ ] **Step 1: Write `src/notifier.py`**

```python
import sys


def send_notification(title: str, message: str) -> None:
    """Send an OS desktop notification. Never raises — failures are logged to stderr."""
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="Claude Desktop Pet",
            timeout=5,
        )
    except Exception as e:
        print(f"[notifier] notification failed: {e}", file=sys.stderr)
```

- [ ] **Step 2: Smoke-test the import**

```bash
python -c "from src.notifier import send_notification; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/notifier.py
git commit -m "[AI开发]feat(notifier): 新增系统通知发送器，防御性封装 plyer"
```

---

## Task 8: Main Window (`src/pet.py`)

**Files:**
- Create: `src/pet.py`

- [ ] **Step 1: Write `src/pet.py`**

```python
import sys
import json
import os
import time
import math
import random
import argparse
from pathlib import Path

# Extend path so sibling packages resolve
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))
sys.path.insert(0, os.path.join(_HERE, "..", "assets"))

from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QFileDialog
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSlot
from PyQt6.QtGui import QPainter

from renderer import PetRenderer
from animator import PetAnimator
from notifier import send_notification

STATE_FILE = Path.home() / ".claude" / "pet-state.json"
CONFIG_FILE = Path.home() / ".claude" / "pet-config.json"
STALE_THRESHOLD = 30  # seconds before forcing idle


class PetWindow(QWidget):
    def __init__(self, project: str = None):
        super().__init__()
        self._renderer = PetRenderer()
        self._animator = PetAnimator(self)
        self._drag_pos: QPoint | None = None
        self._drag_moved = False
        self._last_timestamp = 0
        self._last_update_time = time.time()
        self._project: str | None = None
        self._motion_type = "none"
        self._motion_step = 0
        self._base_pos: QPoint | None = None

        self._setup_window()
        self._animator.frame_changed.connect(self.update)
        self._animator.motion_changed.connect(self._on_motion_changed)

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_state)
        self._poll_timer.start(500)

        self._motion_timer = QTimer(self)
        self._motion_timer.timeout.connect(self._apply_motion)

        if project:
            self._configure_project(project)
        else:
            self._load_config()

        self._animator.start()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(PetRenderer.widget_width(), PetRenderer.widget_height())
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - PetRenderer.widget_width() - 20
        y = screen.height() - PetRenderer.widget_height() - 60
        self.move(x, y)
        self._base_pos = QPoint(x, y)

    # ── Config / project ─────────────────────────────────────────────────────

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                project = cfg.get("project")
                if project and Path(project).exists():
                    self._project = project
                    return
            except Exception:
                pass
        self._project = None
        self._animator.set_state("unconfigured")

    def _configure_project(self, project_dir: str):
        from setup_hooks import install_hooks
        hook_script = os.path.abspath(
            os.path.join(_HERE, "..", "scripts", "hook_writer.py")
        )
        install_hooks(project_dir, sys.executable, hook_script)
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps({"project": project_dir}, ensure_ascii=False),
            encoding="utf-8",
        )
        self._project = project_dir
        self._animator.set_state("idle")

    def _remove_hooks(self):
        if not self._project:
            return
        from setup_hooks import remove_hooks
        hook_script = os.path.abspath(
            os.path.join(_HERE, "..", "scripts", "hook_writer.py")
        )
        remove_hooks(self._project, hook_script)
        self._project = None
        CONFIG_FILE.unlink(missing_ok=True)
        self._animator.set_state("unconfigured")

    # ── Painting ─────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self._renderer.render(painter, self._animator.current_frame())
        painter.end()

    # ── Mouse interaction ─────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._drag_moved = False

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.frameGeometry().topLeft() - self._drag_pos
            if delta.manhattanLength() > 3:
                self._drag_moved = True
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            self._base_pos = new_pos

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._drag_moved and self._animator.state == "unconfigured":
                self._show_config_dialog()
            self._drag_pos = None
            self._drag_moved = False

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        project_name = Path(self._project).name if self._project else "未配置"
        info = menu.addAction(f"📁 {project_name}")
        info.setEnabled(False)
        menu.addSeparator()
        menu.addAction("切换项目…").triggered.connect(self._show_config_dialog)
        menu.addAction("移除当前项目 Hooks").triggered.connect(self._remove_hooks)
        menu.addSeparator()
        menu.addAction("退出").triggered.connect(QApplication.quit)
        menu.exec(event.globalPos())

    def _show_config_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "选择项目文件夹")
        if folder:
            self._configure_project(folder)

    # ── State polling ─────────────────────────────────────────────────────────

    @pyqtSlot()
    def _poll_state(self):
        if not STATE_FILE.exists():
            return
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            ts = data.get("timestamp", 0)
            state = data.get("state", "idle")

            if ts != self._last_timestamp:
                self._last_timestamp = ts
                self._last_update_time = time.time()
                if state == "waiting" and self._animator.state != "waiting":
                    send_notification("Claude Desktop Pet", "Claude 需要你的确认 🔔")
                self._animator.set_state(state)
            else:
                elapsed = time.time() - self._last_update_time
                if elapsed > STALE_THRESHOLD:
                    if self._animator.state not in ("idle", "unconfigured"):
                        self._animator.set_state("idle")
        except Exception:
            pass

    # ── Window motion ─────────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_motion_changed(self, motion_type: str):
        self._motion_type = motion_type
        self._motion_step = 0
        if motion_type != "none":
            self._motion_timer.start(50)
        else:
            self._motion_timer.stop()
            if self._base_pos:
                self.move(self._base_pos)

    @pyqtSlot()
    def _apply_motion(self):
        if not self._base_pos:
            return
        self._motion_step += 1
        bx, by = self._base_pos.x(), self._base_pos.y()
        if self._motion_type == "float":
            offset_y = int(3 * math.sin(self._motion_step * 0.15))
            self.move(bx, by + offset_y)
        elif self._motion_type == "shake":
            self.move(bx + random.randint(-2, 2), by + random.randint(-2, 2))
        elif self._motion_type == "tremble":
            self.move(bx + random.randint(-1, 1), by + random.randint(-1, 1))


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Claude Desktop Pet")
    parser.add_argument("--project", default=None, help="Project dir to monitor immediately")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = PetWindow(project=args.project)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test the app launches**

```bash
python src/pet.py
```

Expected: a small pixel-art pet appears in the bottom-right corner of your screen in dim (unconfigured) state. Close it with right-click → 退出.

- [ ] **Step 3: Commit**

```bash
git add src/pet.py
git commit -m "[AI开发]feat(pet): 新增主浮窗，实现 PyQt6 透明置顶窗口、状态轮询和交互菜单"
```

---

## Task 9: Full Integration Test (Manual)

This task verifies the complete state flow end-to-end.

- [ ] **Step 1: Run the pet**

```bash
python src/pet.py
```

Pet appears dim in bottom-right corner.

- [ ] **Step 2: Configure a project**

Left-click the pet → folder picker appears. Select any directory with a `.claude/` folder (e.g., this repo itself). Confirm.

Expected: pet turns full-color orange with white eyes (idle state). Check that `.claude/settings.json` in the chosen project now contains hook entries referencing `hook_writer.py`.

- [ ] **Step 3: Simulate a hook event**

Open a new terminal and run:

```bash
echo '{"hook_event_name": "PreToolUse", "tool_name": "Read"}' | python scripts/hook_writer.py
```

Expected: `~/.claude/pet-state.json` contains `"state": "reading"`. Pet eyes turn yellow and scan left-right.

- [ ] **Step 4: Simulate all states**

```bash
# thinking
echo '{"hook_event_name": "PreToolUse", "tool_name": "Agent"}' | python scripts/hook_writer.py
# writing
echo '{"hook_event_name": "PreToolUse", "tool_name": "Edit"}' | python scripts/hook_writer.py
# executing
echo '{"hook_event_name": "PreToolUse", "tool_name": "Bash"}' | python scripts/hook_writer.py
# waiting (triggers system notification)
echo '{"hook_event_name": "Notification"}' | python scripts/hook_writer.py
# idle
echo '{"hook_event_name": "Stop"}' | python scripts/hook_writer.py
```

Expected: pet animates through each state. OS notification fires on `waiting`.

- [ ] **Step 5: Test stale timeout**

Simulate a state, then wait 35 seconds without writing new events.

Expected: pet returns to idle state automatically.

- [ ] **Step 6: Test right-click menu**

Right-click the pet. Verify:
- Project name shown as first (disabled) item
- "切换项目…" opens folder picker
- "移除当前项目 Hooks" reverts to unconfigured
- "退出" closes app

- [ ] **Step 7: Run all unit tests**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "[AI开发]test(integration): 完成端到端集成验证"
git push origin main
```

---

## Task 10: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# Claude Desktop Pet

一个悬浮在桌面上的像素宠物，实时显示 Claude Code 的工作状态。

## 状态对应

| 宠物表现 | Claude 正在做 |
|---|---|
| 白眼缓慢浮动 | 待机 |
| 紫眼左右移动 | 思考 / 调用 Agent |
| 黄眼扫描 | 查阅文件 |
| 绿眼 + 进度条 | 写入文件 |
| 宽眼快速抖动 | 执行命令 |
| 红眼闪烁 + 系统通知 | 等待你确认 |

## 安装

```bash
pip install -r requirements.txt
```

## 启动

```bash
python src/pet.py
```

首次启动：点击宠物 → 选择要监听的 Claude Code 项目目录 → 确认。

## 命令行快速启动

```bash
python src/pet.py --project /path/to/your/project
```

## 操作

- **左键拖动**：移动宠物位置
- **右键**：切换项目 / 移除 Hooks / 退出

## 打包为可执行文件

```bash
pip install pyinstaller
pyinstaller --onefile --windowed src/pet.py
```

生成的可执行文件在 `dist/` 目录。
```

- [ ] **Step 2: Commit and push**

```bash
git add README.md
git commit -m "[AI开发]docs(readme): 新增使用说明文档"
git push origin main
```
