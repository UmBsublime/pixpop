# Configuration

Pixpop reads an optional TOML configuration file at startup. Every setting
has a sensible built-in default — you only need the file for the values you
want to change.

## File locations

The first file found wins:

1. `./pixpop-config.toml` — current working directory
2. `~/.config/pixpop/config.toml` — per-user config
3. Built-in defaults

!!! tip
    A ready-to-edit [`pixpop-config-example.toml`](https://github.com/UmBsublime/pixpop/blob/main/pixpop-config-example.toml)
    ships in the repository. Copy it to one of the locations above and
    rename it.

Invalid values are coerced back to defaults (with a warning on stderr), so a
typo never prevents the app from starting.

## Canvas limits

### max_layers

Maximum number of layers per canvas. **Default: `10`**

### min_canvas_width / min_canvas_height

<a id="min_canvas_width"></a> <a id="min_canvas_height"></a>
Smallest allowed canvas dimensions, in pixels. **Default: `4` / `4`**

### default_canvas_width / default_canvas_height

<a id="default_canvas_width"></a> <a id="default_canvas_height"></a>
Dimensions of a new canvas, in pixels. **Default: `128` / `128`**

### max_canvas_width / max_canvas_height

<a id="max_canvas_width"></a> <a id="max_canvas_height"></a>
Largest allowed canvas dimensions, in pixels. **Default: `1024` / `1024`**

## Interaction

### canvas_pan_direction

Direction of the canvas pan gesture (Space+drag, or Ctrl+drag where the
terminal forwards it):

- `"grab"` — the content follows the cursor (like Photoshop/Figma's hand
  tool): dragging right reveals content to the left.
- `"stick"` — the view follows the mouse direction: dragging right scrolls
  the view right.

**Default: `"grab"`**

## Background

The canvas background is the pattern shown behind transparent pixels.

### background_mode

Either `"checker"` (checkerboard) or `"solid"`. **Default: `"checker"`**

### checker_size_width / checker_size_height

Size of each checkerboard square, in pixels. Only applies in `checker` mode.
**Default: `16` / `16`**

### checker_color_a / checker_color_b

The two checkerboard colors, as hex strings. Only applies in `checker` mode.
**Default: `"#2b2b2b"` / `"#313131"`**

### background_color

Background color, as a hex string. Only applies in `solid` mode.
**Default: `"#2b2b2b"`**

## Colors

### default_palette_name

Palette loaded at startup — the name of a bundled `.hex` palette, without
the extension. **Default: `"default"`**

See [Colors & Palettes](colors.md#palettes) for the bundled palette list.

### recent_colors_max

Number of entries kept in the recent colors row. **Default: `8`**

## Editing

### undo_max_entries

Depth of the per-tab undo/redo history. **Default: `50`**

## Appearance

### theme_name

The [Textual theme](https://textual.textualize.io/guide/design/#themes)
used by the interface. **Default: `"twilight-bog"`** (a theme registered by
Pixpop itself; any built-in Textual theme name also works).

## Example

```toml
max_layers = 10
min_canvas_width = 4
min_canvas_height = 4
#default_canvas_width = 128
#default_canvas_height = 128
#max_canvas_width = 1024
#max_canvas_height = 1024
default_palette_name = "default"
checker_size_width = 8
checker_size_height = 8
# Options: solid/checker
background_mode = "checker"
# Only works when background_mode=solid
background_color = "#2b2b2b"
checker_color_a = "#2b2b2b"
checker_color_b = "#313131"
recent_colors_max = 8
undo_max_entries = 50
theme_name = "twilight-bog"
# Options: grab/stick
canvas_pan_direction = "grab"
```
