# Getting Started

## Requirements

- **Python 3.14** or newer
- **[uv](https://docs.astral.sh/uv/)** for dependency management
- A terminal with mouse support and truecolor rendering for the best experience

## Installation

```bash
git clone https://github.com/umbsublime/pixpop.git
cd pixpop
uv sync
```

## Running

```bash
uv run pixpop
```

Or, once installed as a package:

```bash
pixpop
```

## Your first canvas

When Pixpop starts you get a single tab containing a blank canvas, with the
**pen** tool selected and a default palette loaded.

![Pixpop main window](assets/images/app.png)

The screen is organized into a few regions:

| Region | What it does |
|---|---|
| **Tabs** (top) | One tab per open canvas. Switch, rename, add, or close canvases here. |
| **Canvas** (center) | The drawing surface. Paint with the mouse. |
| **Tool picker** (side) | Select the active drawing tool. |
| **Brush / spray pickers** (side) | Adjust brush size or spray density for tools that support it. |
| **Color picker** (side) | Choose the pen color from the active palette. |
| **Layer picker** (side) | Manage layers for the active canvas. |

## A five-minute tour

1. **Paint something.** Left-click and drag on the canvas with the default pen.
2. **Change color.** Click a swatch in the color picker.
3. **Try a shape.** Select the *Line* tool, then click-drag-release on the
   canvas — you get a live preview while dragging.
4. **Add a layer.** Press ++slash++. Paint on the new layer; the layer below
   stays untouched.
5. **Undo a mistake.** Press ++ctrl+z++ as many times as you like;
   ++ctrl+y++ redoes.
6. **Save your work.** Press ++ctrl+s++ and pick the `.pix` format to keep
   the full session (tabs, layers, undo history), or ++ctrl+e++ to export a
   `.png` or `.ans` image.
7. **Get help.** Press ++question++ at any time to see every keybinding.

!!! tip
    Hover almost any button in the side panels to see a tooltip explaining
    what it does.

## Next steps

- [Keyboard Shortcuts](shortcuts.md) — the complete keymap
- [Drawing Tools](tools.md) — what each tool does
- [Configuration](configuration.md) — customize defaults via TOML
