# Colors & Palettes

## The color picker

The color picker in the side panel shows the active palette as a grid of
swatches. Click a swatch to make it the pen color — everything you draw
from that point uses it.

## Palettes

Pixpop bundles a collection of palettes (loaded from `.hex` files), including:

- `default`
- `catppuccin-mocha-16`
- `gruvbox-dark-16`
- `nord-16`
- `solarized-dark-16`
- `monokai-16`
- `twilight-bog-16`
- `arcade-bright-64`, `dungeon-mood-64`, `spriteforge-64`, `vibrantskies-48`
- …and more

Use the palette dropdown above the swatch grid to switch palettes. The
palette loaded at startup is set by
[`default_palette_name`](configuration.md#default_palette_name).

The palette choice is stored in [`.pix` session files](file-formats.md), so
your palette is restored when you reopen a saved session.

## Recent colors

Every color you paint with is added to the **recent colors** row at the top
of the picker, so you can quickly flip between the handful of colors a piece
actually uses. The row size is set by
[`recent_colors_max`](configuration.md#recent_colors_max) (default: 8).

## Picking a color from the canvas

Press ++i++ to sample the color under the cursor — an eyedropper for pulling
a color straight out of your artwork instead of hunting for it in the
palette.

## The color picker dialog

Press ++p++ to open a full color picker (hue/saturation/value sliders plus
RGB, HSV, and hex inputs) in a modal dialog. It opens on the current pen
color; press ++enter++ to apply the picked color or ++escape++ to cancel.
Confirmed colors are added to the recent colors row.
