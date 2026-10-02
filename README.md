# Pixpop

![pixpop logo](https://raw.githubusercontent.com/UmBsublime/pixpop/main/screenshots/pixpop_x4.png)

A TUI paint application built with the [Textual](https://textual.textualize.io/) framework.

Pixpop was originally built to export pixel art as ANSI escape sequences,
but evolved into a simple multi-layer, multi-canvas pixel drawing app.

I mainly use it now to create fun images to spice up my terminal MOTD via [jestsay](https://github.com/UmBsublime/jestsay).

**[Documentation](https://umbsublime.github.io/pixpop/)**

## Features

- Multiple canvases
- Fixed-size canvases with scrollbars (independent of terminal size)
- Multiple layers
- Full mouse and keyboard support (drawing is mouse-only)
- Configuration file for application defaults
- Save and export as .ans, .png, and .pix session files
- Open and load .ans, .png, and .pix session files
- Undo-redo stack
- Help screen and tooltips

## Caveats

This application is designed to draw in the terminal, which comes with limitations.
We are able to draw `pixels` (half-characters), but there is no way to know if the mouse is positioned
on the top or bottom pixel. To work around this, set the pen to brush size 1 (a single pixel) and hold
`Alt` to offset the cursor down by one pixel — painting the bottom half of the cell under the pointer.
The `Alt` offset also applies to the cell, eraser, shape, and light/dark tools.

## Screenshots

<table>
  <tr>
    <td><img src="https://raw.githubusercontent.com/UmBsublime/pixpop/main/screenshots/app.png" alt="Pixpop main window"></td>
    <td><img src="https://raw.githubusercontent.com/UmBsublime/pixpop/main/screenshots/help.png" alt="Pixpop help dialog"></td>
  </tr>
</table>

## Pixpop session format (.pix)

Pixpop supports saving and loading full sessions as `.pix` files. These are
gzipped JSON files that capture:

- Tabs (canvas names and order)
- Canvas size per tab
- Layers, visibility, and pixel data
- Undo/redo stacks per tab
- Shared tool state and palette selection

The `.pix` format is intended for restoring a working session rather than
exporting artwork. For artwork exports, use PNG or ASCII.

## Installation

### Terminal requirements

Pixpop needs two environment variables for full color support:

- `TERM` must be a 256-color variant (e.g. `xterm-256color`)
- `COLORTERM=truecolor` to enable 24-bit true color

Most modern terminals (kitty, alacritty, foot, ghostty, wezterm, GNOME
Terminal, Konsole) set these correctly out of the box. If colors look off,
check with:

```bash
echo $TERM       # should end in -256color
echo $COLORTERM  # should be truecolor
```

With [uv](https://docs.astral.sh/uv/) (recommended):
```bash
uv tool install pixpop
```

With [pipx](https://pipx.pypa.io/):
```bash
pipx install pixpop
```

From source:
```bash
git clone https://github.com/umbsublime/pixpop.git
cd pixpop
uv sync
uv run pixpop
```

## Usage

```bash
pixpop
```

- Draw with the mouse (see [Caveats](#caveats) for single-pixel drawing)
- Press `?` for the help screen and full keybindings
- `Ctrl+S` to save, `Ctrl+E` to export, `Ctrl+O` to load (`.ans`, `.png`, `.pix`)
- Try to `cat` your .ans file in the terminal

See the [documentation](https://umbsublime.github.io/pixpop/) for details.

## Powered by

- [textual](https://github.com/Textualize/textual): TUI framework powering the app shell and widgets.
- [textual-canvas](https://github.com/davep/textual-canvas): Pixel canvas widget used for drawing operations.
- [textual-fspicker](https://github.com/davep/textual-fspicker): File picker dialogs for save/load flows.
- [textual-slider](https://github.com/TomJGooding/textual-slider): Slider widget used for the light/dark step control.
