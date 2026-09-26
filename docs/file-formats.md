# File Formats

Pixpop works with three file formats: `.pix` session files for saving your
whole workspace, and `.png` / `.ans` for exporting finished artwork.

## Saving vs. exporting

| | Save (++ctrl+s++) | Export (++ctrl+e++) |
|---|---|---|
| Purpose | Preserve your working session | Produce shareable artwork |
| Format | `.pix` | `.png` or `.ans` |
| Keeps layers | Yes | No (composited) |
| Keeps undo history | Yes | No |
| Keeps tabs | Yes | No (active canvas only) |

Both dialogs let you type a path directly or browse with the file picker.
If you enter a directory, a timestamped filename is generated for you.
Parent directories are created automatically, and files are written
atomically so a crash never leaves a half-written file.

## .pix — session files

`.pix` is Pixpop's native session format: a gzipped JSON document capturing
everything needed to restore your workspace exactly as you left it:

- Tabs (canvas names and order)
- Canvas size per tab
- Layers — names, visibility, and pixel data
- Undo/redo stacks per tab
- Shared tool state and palette selection

!!! info "Session, not artwork"
    The `.pix` format is meant for restoring a working session, not for
    sharing art. Export to PNG or ANSI for that.

## .png — image export

Exports the active canvas as a PNG image with transparency, compositing all
visible layers. The export dialog offers integer upscaling — **1x, 2x, 4x,
or 8x** — so tiny pixel art can be exported at a viewable size without
blurring.

PNG files can also be **loaded** back onto a canvas (see below), which makes
PNGs a reasonable interchange format for starting from existing art.

## .ans — ANSI art export

Exports the active canvas as ANSI art (escape-coded colored half-blocks),
the classic format for terminal art and BBS-style pieces. The export dialog
offers a **Trim** option that crops the output to the painted region instead
of exporting the full canvas rectangle.

Pixels matching the canvas background are written as transparent, so the
artwork composites cleanly over whatever is behind it in the terminal.

## Loading files (++ctrl+o++)

The load dialog accepts all three formats:

| Format | What happens |
|---|---|
| `.pix` | Restores the full session: tabs, layers, undo history, palette |
| `.png` | Imports the image onto a canvas |
| `.ans` | Parses the ANSI art onto a canvas |

Loaded artwork can be edited with every tool — import a PNG sketch, then
keep drawing on it in the terminal.
