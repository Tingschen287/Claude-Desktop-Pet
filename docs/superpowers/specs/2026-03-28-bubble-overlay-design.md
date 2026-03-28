# Bubble Overlay — Design Spec

**Date:** 2026-03-28
**Status:** Approved

## Overview

When Claude Code requires user confirmation (`Notification` hook event → `waiting` state), a small animated bell bubble appears above the desktop pet to draw the user's attention. The pet's own animation and rendering remain completely unchanged.

## Architecture

Two-component design:

1. **`src/bubble_overlay.py`** — new standalone widget
2. **`src/pet.py`** — minimal additions to create, show, hide, and reposition the overlay

No changes to `renderer.py`, `animator.py`, `frames.py`, or `notifier.py`.

## BubbleOverlay Widget

### Window properties
- Inherits `QWidget`
- Flags: `FramelessWindowHint | WindowStaysOnTopHint | Tool`
- Attribute: `WA_TranslucentBackground`
- Fixed size: ~50 × 34 px (wide enough for 🔔 label + padding)
- Starts hidden (`hide()`)

### Visual appearance
Drawn in `paintEvent` via `QPainter`:
- Yellow rounded rectangle (`#F5C842`, radius 8px), full widget width minus 2px margin on each side
- 🔔 text centered in the rect, font size ~14px
- Small downward-pointing triangle (filled same yellow) centered at the bottom of the rect, pointing toward the pet's head — drawn as a filled polygon

### Shake animation
- `QTimer` at 80 ms interval
- Alternates the widget x-position ±3px from its base position
- Timer runs only while the overlay is visible; stops on `hide_bubble()`

### Public API
```python
def show_bubble(self) -> None   # show + start shake timer
def hide_bubble(self) -> None   # hide + stop shake timer
def reposition(self) -> None    # recalculate position from pet window
```

### Positioning
`reposition()` reads the pet window's current geometry:
```
bubble_x = pet.x() + (pet.width() - bubble.width()) // 2
bubble_y = pet.y() - bubble.height() - 8
```
Called on `show_bubble()` and whenever the pet moves.

## pet.py Changes

### `__init__`
```python
from bubble_overlay import BubbleOverlay
self._bubble = BubbleOverlay(self)
```

### `_poll_state`
```python
if state == "waiting" and self._animator.state != "waiting":
    self._bubble.show_bubble()
elif state != "waiting" and self._animator.state == "waiting":
    self._bubble.hide_bubble()
```
(The existing `notify()` call stays — Windows notification + bubble coexist.)

### `mouseMoveEvent` and `_apply_motion`
Add `self._bubble.reposition()` after every position update so the bubble tracks the pet during drag and float/shake motion.

## State Lifecycle

```
state → waiting   : bubble.show_bubble()   pet animation unchanged
state ← waiting   : bubble.hide_bubble()
pet dragged       : bubble.reposition()
pet floating/shaking: bubble.reposition() (called each motion tick)
app exit          : bubble destroyed with parent window
```

## Testing

- Manual: trigger a `Notification` hook event (or write a `waiting` state to `pet-state.json`) and verify the bubble appears above the pet, shakes, and disappears when state changes.
- No new automated tests required — the overlay is pure UI with no business logic.

## Out of Scope

- Bubble content other than 🔔 (no text message, no dismiss button)
- Multi-monitor repositioning edge cases (future work)
- Custom bubble color/style configuration
