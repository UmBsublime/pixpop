# Pixpop

**A TUI paint application built with the [Textual](https://textual.textualize.io/) framework.**

Pixpop was originally built to export pixel art as ANSI escape sequences,
but evolved into a simple multi-layer, multi-canvas pixel drawing app.
It pairs well with tools like [jestsay](https://github.com/UmBsublime/jestsay)
for spicing up your terminal MOTD.

![Pixpop main window](assets/images/app.png)

## Features

- :material-tab: **Multiple canvases** — work on several pieces at once with tabs
- :material-layers: **Multiple layers** — stack, reorder, hide, and rename layers
- :material-mouse: **Full mouse and keyboard support** — drawing is mouse-only, everything else has a [shortcut](shortcuts.md)
- :material-cog: **Configuration file** — set application [defaults](configuration.md) via TOML
- :material-content-save: **Save & export** — `.ans`, `.png`, and `.pix` [session files](file-formats.md)
- :material-folder-open: **Open & load** — import `.ans`, `.png`, and `.pix` files
- :material-undo: **Undo/redo stack** — per-tab history
- :material-help-circle: **Built-in help** — press ++question++ anywhere for the shortcut reference

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

### Install

=== "uv (recommended)"

    ```bash
    uv tool install pixpop
    ```

=== "pipx"

    ```bash
    pipx install pixpop
    ```

=== "From source"

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

- Draw with the mouse (see the [caveat](#the-half-character-caveat) below for the [fine pen](tools.md#fine-pen))
- Press ++question++ for the [help screen and full keybindings](shortcuts.md)
- ++ctrl+s++ to save, ++ctrl+e++ to export, ++ctrl+o++ to load (`.ans`, `.png`, `.pix`)
- Try `cat`-ing your `.ans` file back into the terminal

See [Getting Started](getting-started.md) for a full tour.

## The half-character caveat

Pixpop draws in the terminal using *half characters*: each terminal cell is two
stacked pixels (`▀`). The mouse can only report which **cell** it is over — not
whether it is on the top or bottom pixel of that cell. The
[Fine pen](tools.md#fine-pen) works around this:

- **Left-click** paints the top pixel
- **Right-click** paints the bottom pixel
- **Middle-click** paints both pixels

## Powered by

- [textual](https://github.com/Textualize/textual) — TUI framework powering the app shell and widgets
- [textual-canvas](https://github.com/davep/textual-canvas) — pixel canvas widget used for drawing
- [textual-fspicker](https://github.com/davep/textual-fspicker) — file picker dialogs for save/load flows
