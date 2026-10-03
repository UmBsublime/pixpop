# Canvases & Tabs

Pixpop lets you keep several canvases open at once — one per tab. Each tab
has its own size, layers, and undo/redo history.

## Working with tabs

| Action | Keys | Notes |
|---|---|---|
| New tab | ++t++ | Asks for a canvas size, then creates a fresh canvas |
| Switch tab | ++n++ | Cycles to the next tab (wraps around) |
| Rename tab | ++r++ | Opens a rename dialog |
| Close tab | ++ctrl+w++ | Closes the active tab |

You can also click a tab to switch to it.

Press ++f++ to toggle the tab area fullscreen: the side panel and header are
hidden and the canvas tabs take over the window (the footer stays). Press
++f++ again to restore the normal layout.

The tab name is used as the default project name in the
[save dialog](file-formats.md), so renaming tabs keeps exported files tidy.

## Canvas size

Each canvas has a fixed size in pixels, chosen when the tab is created —
it does not resize with the terminal window. When a canvas is larger than
the visible area, scrollbars appear; scroll by clicking or dragging them,
or pan by holding ++space++ and dragging the canvas. (Ctrl+drag also pans
in terminals that forward modifier+mouse events — under tmux you'll want
the space gesture, since tmux's default bindings capture Ctrl+click.) See
[`canvas_pan_direction`](configuration.md#canvas_pan_direction) to choose
the gesture direction.

By default a new canvas fills the available space, so no scrollbars are
needed — unless
[`default_canvas_width`](configuration.md#default_canvas_width) /
[`default_canvas_height`](configuration.md#default_canvas_height) are set
in the config file, in which case new canvases start at that size instead.
Pressing ++t++ opens a dialog asking for the new canvas's width
and height, pre-filled with that starting size (or your last chosen size
from the same session), so repeatedly creating same-sized canvases is a
single ++enter++ away.

Default and limit sizes are configurable:

- [`default_canvas_width`](configuration.md#default_canvas_width) /
  [`default_canvas_height`](configuration.md#default_canvas_height)
- [`min_canvas_width`](configuration.md#min_canvas_width) /
  [`min_canvas_height`](configuration.md#min_canvas_height)
- [`max_canvas_width`](configuration.md#max_canvas_width) /
  [`max_canvas_height`](configuration.md#max_canvas_height)

The starting size — viewport-fit or configured default — is clamped
between the configured min and max sizes.

A canvas smaller than the visible area is centered in its tab; the space
around it shows the panel background. Centering follows the window size, so
resizing the terminal or toggling [fullscreen](#working-with-tabs) recenters
the canvas.

## Flipping artwork

The **Flip** picker mirrors artwork with a single click:

| Mode | Effect |
|---|---|
| **Vertical** | Mirrors the whole canvas about the vertical axis (left ↔ right) |
| **Horizontal** | Mirrors the whole canvas about the horizontal axis (top ↔ bottom) |
| **Layer Vertical** | Mirrors only the active layer, left ↔ right |
| **Layer Horizontal** | Mirrors only the active layer, top ↔ bottom |

Whole-canvas flips remap every layer; layer flips leave the rest of the
stack untouched. Flips are undoable like any other edit.

## Clearing and history

- ++c++ clears the active canvas (undoable).
- ++ctrl+z++ / ++ctrl+y++ step through the per-tab undo/redo history.
  History depth is set by [`undo_max_entries`](configuration.md#undo_max_entries)
  (default: 50).

## Canvas background

The checkerboard shown behind transparent pixels is configurable — size,
colors, or a solid background instead. See
[Configuration → Background](configuration.md#background).
