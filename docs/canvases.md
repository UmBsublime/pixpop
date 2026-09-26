# Canvases & Tabs

Pixpop lets you keep several canvases open at once — one per tab. Each tab
has its own size, layers, and undo/redo history.

## Working with tabs

| Action | Keys | Notes |
|---|---|---|
| New tab | ++t++ | Creates a fresh canvas |
| Switch tab | ++n++ | Cycles to the next tab (wraps around) |
| Rename tab | ++r++ | Opens a rename dialog |
| Close tab | ++ctrl+w++ | Closes the active tab |

You can also click a tab to switch to it.

The tab name is used as the default project name in the
[save dialog](file-formats.md), so renaming tabs keeps exported files tidy.

## Canvas size

The canvas automatically fills the available space and resizes with the
terminal window — existing artwork is preserved when the canvas grows or
shrinks.

Default and limit sizes are configurable:

- [`default_canvas_width`](configuration.md#default_canvas_width) /
  [`default_canvas_height`](configuration.md#default_canvas_height)
- [`min_canvas_width`](configuration.md#min_canvas_width) /
  [`min_canvas_height`](configuration.md#min_canvas_height)
- [`max_canvas_width`](configuration.md#max_canvas_width) /
  [`max_canvas_height`](configuration.md#max_canvas_height)

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
